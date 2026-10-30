"""Package the runnable Cursor helper closure separately from the native plugin."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("delivery_native", ROOT / "scripts/cursor_release.py")
assert SPEC is not None and SPEC.loader is not None
native = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)

NAME = "guardtrellis-cursor-helper"
VERSION = "0.1.0-preview.4"
MANIFEST = "DELIVERY-MANIFEST.json"
NATIVE_PATH = "artifacts/guardtrellis-cursor-0.1.0-preview.4-advisory.zip"
NATIVE_SHA256 = "1dd58f7d6d165db44708608f608691c4945a4ef719dd6ffafe6f7a500bcb691b"
MAX_BYTES = 32 * 1024 * 1024
MAX_TEXT_BYTES = 512 * 1024
SOURCE_FILES = {
    "README.md": "integrations/cursor/delivery/README.md",
    "SUPPORT.md": "integrations/cursor/delivery/SUPPORT.md",
    "LICENSE": "plugins/guardtrellis/LICENSE",
    "NOTICE": "integrations/cursor/plugin/NOTICE",
    "scripts/cursor_delivery.py": "scripts/cursor_delivery.py",
    "scripts/cursor_workspace.py": "scripts/cursor_workspace.py",
    "scripts/cursor_release.py": "scripts/cursor_release.py",
    "integrations/cursor/bootstrap.py": "integrations/cursor/bootstrap.py",
}
PAYLOAD_FILES = (*SOURCE_FILES, NATIVE_PATH)


class DeliveryError(Exception):
    """Static, non-sensitive delivery failure."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def _read(file: Path, limit: int) -> bytes:
    if any(item.is_symlink() for item in (file, *file.parents)) or not file.is_file():
        raise DeliveryError("Selected input must be a regular unlinked file.")
    with file.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise DeliveryError("Selected input exceeds its size limit.")
    return data


def _native_record() -> dict[str, Any]:
    return {
        "path": NATIVE_PATH,
        "sha256": NATIVE_SHA256,
        "profile": "advisory",
        "version": native.VERSION,
        "source_files": 22,
        "sdk_version": "0.1.9",
    }


def _verify_native(payload: bytes) -> None:
    if digest(payload) != NATIVE_SHA256:
        raise DeliveryError("Embedded native artifact differs from the approved advisory ZIP.")
    with tempfile.TemporaryDirectory(prefix="gt-delivery-native-") as temporary:
        archive = Path(temporary) / "native.zip"
        archive.write_bytes(payload)
        files = native.verify(archive, NATIVE_SHA256)
    if native.read_json(files[native.MANIFEST])["profile"] != "advisory":
        raise DeliveryError("Only the approved advisory native artifact is supported.")


def _fresh(destination: Path) -> Path:
    if not destination.is_absolute() or destination != destination.resolve():
        raise DeliveryError("Select an absolute canonical destination.")
    if any(item.is_symlink() for item in (destination, *destination.parents)):
        raise DeliveryError("Linked destination paths are not supported.")
    if destination.exists() or not destination.parent.is_dir():
        raise DeliveryError("Destination must be fresh and its parent must exist.")
    home = Path.home().resolve()
    profiles = [home / name for name in (".codex", ".claude", ".cursor")]
    profiles.append(home / "Library/Application Support/Cursor")
    if destination == home or any(destination.is_relative_to(path) for path in profiles):
        raise DeliveryError("Writing into a normal agent profile is not supported.")
    return destination


def _parent_fd(destination: Path) -> int:
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in destination.parent.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError:
        os.close(descriptor)
        raise


def _write_fresh(destination: Path, files: dict[str, bytes]) -> None:
    destination = _fresh(destination)
    parent = _parent_fd(destination)
    root = -1
    try:
        os.mkdir(destination.name, mode=0o700, dir_fd=parent)
        root = os.open(
            destination.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
        )
        for name, data in files.items():
            directory = os.dup(root)
            try:
                parts = Path(name).parts
                for part in parts[:-1]:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=directory)
                    except FileExistsError:
                        pass
                    child = os.open(
                        part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
                    )
                    os.close(directory)
                    directory = child
                descriptor = os.open(
                    parts[-1],
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(data)
            finally:
                os.close(directory)
    finally:
        if root != -1:
            os.close(root)
        os.close(parent)


def build(source: Path, output: Path, native_archive: Path, native_sha256: str) -> dict[str, Any]:
    if native_sha256.lower() != NATIVE_SHA256:
        raise DeliveryError("A trusted checksum for the approved native artifact is required.")
    source = source.resolve()
    files = {
        name: _read(source / original, MAX_TEXT_BYTES) for name, original in SOURCE_FILES.items()
    }
    files[NATIVE_PATH] = _read(native_archive, native.MAX_BYTES)
    _verify_native(files[NATIVE_PATH])
    manifest = encoded(
        {
            "format": 1,
            "name": NAME,
            "version": VERSION,
            "native": _native_record(),
            "files": {name: digest(data) for name, data in files.items()},
        }
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted({**files, MANIFEST: manifest}.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, data)
    payload = buffer.getvalue()
    if len(payload) > MAX_BYTES:
        raise DeliveryError("Delivery exceeds the archive size limit.")
    filename = f"{NAME}-{VERSION}.zip"
    checksums = f"{digest(payload)}  {filename}\n{digest(manifest)}  {MANIFEST}\n".encode()
    _write_fresh(
        output,
        {
            filename: payload,
            MANIFEST: manifest,
            "SHA256SUMS": checksums,
        },
    )
    return {
        "archive": str(output / filename),
        "sha256": digest(payload),
        "bytes": len(payload),
        "payload_files": len(files),
        "members": len(files) + 1,
        "native_sha256": NATIVE_SHA256,
        "publication": "not_performed",
    }


def verify(archive: Path, checksum: str) -> dict[str, bytes]:
    if not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
        raise DeliveryError("A trusted SHA-256 checksum is required.")
    payload = _read(archive, MAX_BYTES)
    if digest(payload) != checksum.lower():
        raise DeliveryError("Delivery checksum does not match.")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as packed:
            infos = packed.infolist()
            names = [native.safe_name(item.filename) for item in infos]
            if len(set(name.casefold() for name in names)) != len(names):
                raise DeliveryError("Duplicate or case-colliding delivery paths.")
            if (
                set(names) != {*PAYLOAD_FILES, MANIFEST}
                or sum(item.file_size for item in infos) > MAX_BYTES
            ):
                raise DeliveryError("Delivery source list or unpacked size changed.")
            for item in infos:
                mode = item.external_attr >> 16
                if (
                    item.orig_filename != item.filename
                    or item.flag_bits & 1
                    or item.is_dir()
                    or item.compress_type != zipfile.ZIP_STORED
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                ):
                    raise DeliveryError("Delivery permits only stored regular unencrypted files.")
                if item.filename != NATIVE_PATH and item.file_size > MAX_TEXT_BYTES:
                    raise DeliveryError("Delivery text exceeds its size limit.")
            files = {name: packed.read(name) for name in names}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, ValueError, OSError):
        raise DeliveryError("Invalid delivery archive.") from None
    record = native.read_json(files[MANIFEST])
    if (
        set(record) != {"format", "name", "version", "native", "files"}
        or type(record.get("format")) is not int
        or record.get("format") != 1
        or record.get("name") != NAME
        or record.get("version") != VERSION
        or record.get("native") != _native_record()
        or record.get("files") != {name: digest(files[name]) for name in PAYLOAD_FILES}
    ):
        raise DeliveryError("Delivery manifest integrity check failed.")
    _verify_native(files[NATIVE_PATH])
    return files


def extract(archive: Path, checksum: str, destination: Path) -> dict[str, Any]:
    files = verify(archive, checksum)
    _write_fresh(destination, files)
    return {
        "destination": str(destination),
        "files": len(files),
        "native_sha256": NATIVE_SHA256,
        "activation": "not_performed",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    builder = commands.add_parser("build")
    builder.add_argument("--source", type=Path, default=ROOT)
    builder.add_argument("--native-archive", type=Path, required=True)
    builder.add_argument("--native-sha256", required=True)
    builder.add_argument("--output", type=Path, required=True)
    for name in ("verify", "extract"):
        command = commands.add_parser(name)
        command.add_argument("archive", type=Path)
        command.add_argument("--sha256", required=True)
        if name == "extract":
            command.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build(args.source, args.output, args.native_archive, args.native_sha256)
        elif args.command == "extract":
            result = extract(args.archive, args.sha256, args.dest)
        else:
            files = verify(args.archive, args.sha256)
            result = {"verified": True, "files": len(files), "native_sha256": NATIVE_SHA256}
    except (DeliveryError, native.ReleaseError, OSError, ValueError, TypeError, RuntimeError):
        print('{"status":"failed","reason":"delivery_validation_failed"}', file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
