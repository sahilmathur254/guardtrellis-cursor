"""Build and verify the separate, experimental native Cursor plugin source package."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import sys
import tomllib
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

NAME = "guardtrellis-cursor"
VERSION = "0.1.0-preview.3"
MANIFEST = "SOURCE-MANIFEST.json"
MAX_BYTES = 16 * 1024 * 1024
PROFILES = ("advisory", "enforce-secrets-v1")
TEMPLATE = "integrations/cursor/plugin"
EXISTING = "plugins/guardtrellis"
GENERATED = "plugins/guardtrellis-cursor"
CATALOG = ".cursor-plugin/marketplace.json"
CATALOG_NAME = "guardtrellis-cursor-marketplace"
MAX_CATALOG_BYTES = 64 * 1024
MAX_EXPORT_ENTRIES = 512
TEMPLATE_FILES = (
    ".cursor-plugin/plugin.json",
    "hooks/hooks.json",
    "scripts/guardtrellis.sh",
    "scripts/runtime_setup.py",
    "commands/guardtrellis-setup.md",
    "commands/guardtrellis-health.md",
    "commands/guardtrellis-prepare.md",
    "commands/guardtrellis-remove.md",
    "README.md",
    "COMPATIBILITY.md",
    "PRIVACY.md",
    "SUPPORT.md",
)
COPIED_FILES = (
    "LICENSE",
    "assets/logo.svg",
)
SOURCE_MAP = {
    **{name: f"{TEMPLATE}/{name}" for name in TEMPLATE_FILES},
    **{name: f"{EXISTING}/{name}" for name in COPIED_FILES},
    "NOTICE": f"{TEMPLATE}/NOTICE",
    "adapters/common/__init__.py": f"{EXISTING}/adapters/common/__init__.py",
    "adapters/common/prompt_runtime.py": f"{EXISTING}/adapters/common/prompt_runtime.py",
    "adapters/codex/redact_prompt.py": f"{EXISTING}/adapters/codex/redact_prompt.py",
    "adapters/cursor/prompt_check.py": f"{EXISTING}/adapters/cursor/prompt_check.py",
    "adapters/cursor/prepare_prompt.py": f"{EXISTING}/adapters/cursor/prepare_prompt.py",
    "runtime/pyproject.toml": f"{EXISTING}/adapters/codex/pyproject.toml",
    "runtime/uv.lock": f"{EXISTING}/adapters/codex/uv.lock",
}


class ReleaseError(Exception):
    """A source package failed its bounded verification contract."""


class ExportDriftError(ReleaseError):
    """Read-only comparison found generated-source or catalog drift."""

    def __init__(self, differences: dict[str, list[str]]) -> None:
        self.differences = differences
        super().__init__("Generated native export differs from its maintained sources.")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    if (
        not isinstance(name, str)
        or not name
        or "\\" in name
        or ":" in name
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
        or name.startswith("/")
        or any(part in ("", ".", "..") for part in name.split("/"))
        or PurePosixPath(name).is_absolute()
    ):
        raise ReleaseError("Unsafe source path.")
    return name


def read_json(data: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    try:
        value = json.loads(
            data,
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (ValueError, UnicodeError, RecursionError):
        raise ReleaseError("Invalid JSON source metadata.") from None
    if not isinstance(value, dict):
        raise ReleaseError("Source metadata must be an object.")
    return value


def hooks(profile: str) -> dict[str, Any]:
    if profile not in PROFILES:
        raise ReleaseError("Unsupported experimental profile.")
    return {
        "version": 1,
        "hooks": {
            "beforeSubmitPrompt": [
                {
                    "command": "/bin/sh ./scripts/guardtrellis.sh hook"
                    + ("" if profile == "advisory" else " --profile enforce-secrets-v1"),
                    "timeout": 2,
                    "failClosed": profile == "enforce-secrets-v1",
                }
            ]
        },
    }


def validate(files: dict[str, bytes], profile: str) -> None:
    if set(files) != set(SOURCE_MAP):
        raise ReleaseError("Native plugin source list changed.")
    metadata = read_json(files[".cursor-plugin/plugin.json"])
    allowed = {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "logo",
        "hooks",
        "commands",
    }
    if (
        set(metadata) - allowed
        or metadata.get("name") != NAME
        or metadata.get("version") != VERSION
    ):
        raise ReleaseError("Native plugin identity or component scope changed.")
    if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
        raise ReleaseError("Native plugin description is missing.")
    author = metadata.get("author")
    if (
        not isinstance(author, dict)
        or set(author) - {"name", "email"}
        or not isinstance(author.get("name"), str)
    ):
        raise ReleaseError("Native plugin author metadata is invalid.")
    if any(not isinstance(value, str) for value in author.values()):
        raise ReleaseError("Native plugin author metadata is invalid.")
    keywords = metadata.get("keywords", [])
    if not isinstance(keywords, list) or any(not isinstance(value, str) for value in keywords):
        raise ReleaseError("Native plugin keywords are invalid.")
    if any(
        key in metadata and not isinstance(metadata[key], str)
        for key in ("homepage", "repository", "license")
    ):
        raise ReleaseError("Native plugin links or license metadata are invalid.")
    for key, expected in (
        ("hooks", "hooks/hooks.json"),
        ("commands", "commands"),
        ("logo", "assets/logo.svg"),
    ):
        value = metadata.get(key)
        if not isinstance(value, str) or value.removeprefix("./").rstrip("/") != expected:
            raise ReleaseError("Native plugin component paths changed.")
    configured = read_json(files["hooks/hooks.json"])
    if configured != hooks(profile):
        raise ReleaseError("Native hook profile or failure contract changed.")
    definition = configured["hooks"]["beforeSubmitPrompt"][0]
    if (
        type(configured["version"]) is not int
        or type(definition["timeout"]) is not int
        or definition["failClosed"] is not (profile == "enforce-secrets-v1")
    ):
        raise ReleaseError("Native hook configuration types are invalid.")
    try:
        project = tomllib.loads(files["runtime/pyproject.toml"].decode())
        lock = tomllib.loads(files["runtime/uv.lock"].decode())
        dependencies = project.get("project", {}).get("dependencies")
        packages = lock.get("package", [])
        sdk = [
            item
            for item in packages
            if isinstance(item, dict) and item.get("name") == "guardtrellis"
        ]
        if (
            dependencies != ["guardtrellis==0.1.9"]
            or len(sdk) != 1
            or sdk[0].get("version") != "0.1.9"
        ):
            raise ValueError
    except (ValueError, TypeError, AttributeError, UnicodeError):
        raise ReleaseError("Native runtime requires the exact supported SDK pin.") from None
    for command in (name for name in SOURCE_MAP if name.startswith("commands/")):
        if not files[command].startswith(b"---\n") or b"description:" not in files[command]:
            raise ReleaseError("Native command frontmatter is invalid.")
    if b"Apache License" not in files["LICENSE"] or len(files["README.md"].split()) < 40:
        raise ReleaseError("Native package usage or license text is missing.")


def _assembled(source: Path, profile: str) -> tuple[dict[str, bytes], bytes]:
    if profile not in PROFILES:
        raise ReleaseError("Unsupported experimental profile.")
    source = source.resolve()
    files = {}
    for name, original in SOURCE_MAP.items():
        path = source / original
        if not path.is_file() or any(
            entry.is_symlink() for entry in (path, *path.parents) if entry != source
        ):
            raise ReleaseError("Selected source is missing or linked.")
        files[name] = path.read_bytes()
    if read_json(files["hooks/hooks.json"]) != hooks("advisory"):
        raise ReleaseError("The source template must retain the default advisory hook.")
    files["hooks/hooks.json"] = (json.dumps(hooks(profile), indent=2) + "\n").encode()
    validate(files, profile)
    manifest = (
        json.dumps(
            {
                "format": 1,
                "name": NAME,
                "version": VERSION,
                "profile": profile,
                "files": {name: digest(data) for name, data in sorted(files.items())},
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode()
    return files, manifest


def build(source: Path, output: Path, profile: str = "advisory") -> dict[str, Any]:
    files, manifest = _assembled(source, profile)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted({**files, MANIFEST: manifest}.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, data)
    payload = buffer.getvalue()
    if len(payload) > MAX_BYTES:
        raise ReleaseError("Native archive exceeds the source size limit.")
    output.mkdir(parents=True, exist_ok=False)
    filename = f"{NAME}-{VERSION}-{profile}.zip"
    (output / filename).write_bytes(payload)
    (output / MANIFEST).write_bytes(manifest)
    (output / "SHA256SUMS").write_text(
        f"{digest(payload)}  {filename}\n{digest(manifest)}  {MANIFEST}\n"
    )
    return {
        "archive": str((output / filename).resolve()),
        "sha256": digest(payload),
        "profile": profile,
        "source_files": len(files),
    }


def _unlinked(path: Path, source: Path) -> bool:
    return not any(entry.is_symlink() for entry in (path, *path.parents) if entry != source)


def _normal_profile(path: Path, source: Path) -> bool:
    profiles = [Path.home() / name for name in (".claude", ".cursor")]
    profiles.append(Path.home() / "Library/Application Support/Cursor")
    resolved = path.resolve()
    if any(resolved.is_relative_to(profile.resolve()) for profile in profiles):
        return True
    codex = (Path.home() / ".codex").resolve()
    managed_worktrees = (Path.home() / ".codex/worktrees").resolve()
    if not resolved.is_relative_to(codex):
        return False
    git = source / ".git"
    return not (
        resolved.is_relative_to(managed_worktrees) and git.is_file() and not git.is_symlink()
    )


def export(source: Path) -> dict[str, Any]:
    """Write the advisory indexed tree once; an existing tree is never repaired."""
    source = source.resolve()
    destination = source / GENERATED
    if destination.exists() or destination.is_symlink():
        raise ReleaseError("Export requires a fresh canonical destination; inspect drift first.")
    if not _unlinked(destination, source) or _normal_profile(destination, source):
        raise ReleaseError("Export destination is linked or inside a normal agent profile.")
    files, manifest = _assembled(source, "advisory")
    files[MANIFEST] = manifest
    destination.mkdir(parents=True)
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {
        "destination": str(destination),
        "profile": "advisory",
        "files": len(files),
        "source_files": len(files) - 1,
        "manifest_sha256": digest(manifest),
        "catalog": "not_written",
        "hook_activation": "not_performed",
    }


def _catalog_differences(source: Path) -> list[str]:
    path = source / CATALOG
    if not _unlinked(path, source):
        return ["linked_catalog_path"]
    if not path.is_file():
        return ["missing_catalog"]
    if path.stat().st_size > MAX_CATALOG_BYTES:
        return ["catalog_size_limit"]
    try:
        with path.open("rb") as handle:
            catalog = read_json(handle.read(MAX_CATALOG_BYTES + 1))
        if set(catalog) != {"name", "owner", "metadata", "plugins"}:
            return ["catalog_root_fields"]
        if catalog["name"] != CATALOG_NAME:
            return ["catalog_identity"]
        owner, metadata = catalog["owner"], catalog["metadata"]
        if not isinstance(owner, dict) or set(owner) != {"name"}:
            return ["catalog_owner_fields"]
        if not isinstance(metadata, dict) or set(metadata) != {"description", "version"}:
            return ["catalog_metadata_fields"]
        if not isinstance(owner["name"], str) or not owner["name"].strip():
            return ["catalog_owner_type"]
        if not all(isinstance(value, str) and value.strip() for value in metadata.values()):
            return ["catalog_metadata_types"]
        if metadata["version"] != VERSION:
            return ["catalog_version"]
        if catalog["plugins"] != [{"name": NAME, "source": "./" + GENERATED}]:
            return ["catalog_plugin_source_or_fields"]
    except (ReleaseError, OSError):
        return ["invalid_catalog"]
    return []


def check_export(source: Path, *, check_catalog: bool = True) -> dict[str, Any]:
    """Compare canonical files and catalog without writing or following links."""
    source = source.resolve()
    files, manifest = _assembled(source, "advisory")
    files[MANIFEST] = manifest
    destination = source / GENERATED
    expected_dirs = {
        parent.as_posix()
        for name in files
        for parent in PurePosixPath(name).parents
        if parent != PurePosixPath(".")
    }
    found: set[str] = set()
    differences: dict[str, list[str]] = {
        name: []
        for name in ("missing", "modified", "extra", "unsafe", "case_collisions", "catalog")
    }
    if not _unlinked(destination, source) or (destination.exists() and not destination.is_dir()):
        differences["unsafe"].append(GENERATED)
    elif destination.is_dir():
        pending = [(destination, "")]
        seen: dict[str, str] = {}
        entries = 0
        while pending:
            directory, prefix = pending.pop()
            with os.scandir(directory) as children:
                for child in children:
                    entries += 1
                    if entries > MAX_EXPORT_ENTRIES:
                        differences["unsafe"].append("export_entry_limit")
                        pending.clear()
                        break
                    name = prefix + child.name
                    lower = name.casefold()
                    if lower in seen and seen[lower] != name:
                        differences["case_collisions"].extend((seen[lower], name))
                    seen[lower] = name
                    try:
                        safe_name(name)
                    except ReleaseError:
                        differences["unsafe"].append(name)
                        continue
                    if child.is_symlink():
                        differences["unsafe"].append(name)
                    elif child.is_dir(follow_symlinks=False):
                        if name in expected_dirs:
                            pending.append((Path(child.path), name + "/"))
                        else:
                            differences["extra"].append(name + "/")
                    elif child.is_file(follow_symlinks=False):
                        if name not in files:
                            differences["extra"].append(name)
                        else:
                            found.add(name)
                            with open(child.path, "rb") as handle:
                                actual = handle.read(len(files[name]) + 1)
                            if actual != files[name]:
                                differences["modified"].append(name)
                    else:
                        differences["unsafe"].append(name)
    differences["missing"] = sorted(set(files) - found)
    if check_catalog:
        differences["catalog"] = _catalog_differences(source)
    differences = {key: sorted(set(values)) for key, values in differences.items() if values}
    if differences:
        raise ExportDriftError(differences)
    return {
        "verified": True,
        "destination": str(destination),
        "profile": "advisory",
        "files": len(files),
        "source_files": len(files) - 1,
        "manifest_sha256": digest(manifest),
        "catalog": "checked" if check_catalog else "not_requested",
    }


def verify(archive: Path, checksum: str) -> dict[str, bytes]:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", checksum):
        raise ReleaseError("A trusted SHA-256 checksum is required.")
    if archive.is_symlink() or not archive.is_file():
        raise ReleaseError("Archive must be a regular non-symlink file.")
    with archive.open("rb") as handle:
        payload = handle.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES or digest(payload) != checksum.lower():
        raise ReleaseError("Archive size or checksum does not match.")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as packed:
            infos = packed.infolist()
            names = [safe_name(info.filename) for info in infos]
            if len(set(name.casefold() for name in names)) != len(names):
                raise ReleaseError("Duplicate or case-colliding archive paths.")
            if (
                set(names) != {*SOURCE_MAP, MANIFEST}
                or sum(item.file_size for item in infos) > MAX_BYTES
            ):
                raise ReleaseError("Archive source list or unpacked size changed.")
            for item in infos:
                mode = item.external_attr >> 16
                if (
                    item.flag_bits & 1
                    or item.is_dir()
                    or item.compress_type != zipfile.ZIP_STORED
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                ):
                    raise ReleaseError(
                        "Only stored unencrypted regular source files are supported."
                    )
            files = {name: packed.read(name) for name in names}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError, ValueError):
        raise ReleaseError("Invalid native archive.") from None
    manifest = files.pop(MANIFEST)
    record = read_json(manifest)
    if (
        set(record) != {"format", "name", "version", "profile", "files"}
        or type(record.get("format")) is not int
        or record.get("format") != 1
        or record.get("name") != NAME
        or record.get("version") != VERSION
        or record.get("profile") not in PROFILES
        or record.get("files") != {name: digest(data) for name, data in files.items()}
    ):
        raise ReleaseError("Native source manifest integrity failed.")
    validate(files, record["profile"])
    files[MANIFEST] = manifest
    return files


def extract(archive: Path, checksum: str, destination: Path) -> dict[str, Any]:
    files = verify(archive, checksum)
    if destination.exists() or destination.is_symlink():
        raise ReleaseError("Extraction requires a fresh destination.")
    destination = destination.expanduser().absolute()
    profiles = [Path.home() / name for name in (".codex", ".claude", ".cursor")]
    profiles.append(Path.home() / "Library/Application Support/Cursor")
    if any(destination.resolve().is_relative_to(path.resolve()) for path in profiles):
        raise ReleaseError("Extraction into a normal agent profile is not supported.")
    destination.mkdir(parents=True)
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {
        "destination": str(destination.resolve()),
        "files": len(files),
        "hook_activation": "not_performed",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    builder = commands.add_parser("build")
    builder.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    builder.add_argument("--output", type=Path, required=True)
    builder.add_argument("--profile", choices=PROFILES, default="advisory")
    for name in ("export", "check-export"):
        command = commands.add_parser(name)
        command.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
        if name == "check-export":
            command.add_argument("--skip-catalog", action="store_true")
    for name in ("verify", "extract"):
        command = commands.add_parser(name)
        command.add_argument("archive", type=Path)
        command.add_argument("--sha256", required=True)
        if name == "extract":
            command.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build(args.source, args.output, args.profile)
        elif args.command == "export":
            result = export(args.source)
        elif args.command == "check-export":
            result = check_export(args.source, check_catalog=not args.skip_catalog)
        elif args.command == "extract":
            result = extract(args.archive, args.sha256, args.dest)
        else:
            files = verify(args.archive, args.sha256)
            result = {
                "verified": True,
                "files": len(files),
                "profile": read_json(files[MANIFEST])["profile"],
            }
    except (ReleaseError, OSError) as error:
        failure: dict[str, Any] = {"status": "failed", "reason": "native_package_validation_failed"}
        if isinstance(error, ExportDriftError):
            failure.update(reason="native_export_drift", differences=error.differences)
        print(
            json.dumps(failure, sort_keys=True),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
