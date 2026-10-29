"""Explicit ownership-aware project staging; never starts Cursor or sets GUI state."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def module(name: str, file: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, file)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


release = module("workspace_release", ROOT / "scripts/cursor_release.py")
boot = module("workspace_bootstrap", ROOT / "integrations/cursor/bootstrap.py")


def encoded(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()


def _workspace(value: Path) -> Path:
    result: Path = boot.path(value)
    if (
        boot.protected(result)
        or not result.is_dir()
        or result.is_relative_to(ROOT)
        or ROOT.is_relative_to(result)
    ):
        raise boot.StateError("unsafe_workspace")
    return result


def _prepare(
    workspace: Path, archive: Path, checksum: str, python: Path, runtime: Path
) -> tuple[dict[str, Any], dict[str, bytes], bytes, dict[str, Any], bytes | None, int]:
    workspace = _workspace(workspace)
    runtime = boot.path(runtime)
    if (
        boot.protected(runtime)
        or runtime.is_relative_to(workspace)
        or workspace.is_relative_to(runtime)
        or runtime.is_relative_to(ROOT)
        or ROOT.is_relative_to(runtime)
    ):
        raise boot.StateError("unsafe_runtime")
    if not python.is_absolute():
        raise boot.StateError("unsafe_python")
    try:
        python = python.resolve(strict=True)
    except (OSError, RuntimeError):
        raise boot.StateError("bootstrap_python_unavailable") from None
    if not python.is_file() or not os.access(python, os.X_OK):
        raise boot.StateError("bootstrap_python_unavailable")
    control = workspace / boot.CONTROL
    boot.path(control)
    if control.exists():
        raise boot.StateError("owned_control_already_exists")
    files = release.verify(archive, checksum)
    if (
        set(files) != boot.PLUGIN_FILES
        or release.read_json(files[release.MANIFEST])["profile"] != "advisory"
    ):
        raise boot.StateError("advisory_archive_required")
    current, raw, mode = boot.config(workspace)
    for entries in current.get("hooks", {}).values():
        if any(
            isinstance(entry.get("command"), str) and str(control) in entry["command"]
            for entry in entries
        ):
            raise boot.StateError("unknown_existing_owned_reference")
    bootstrap = boot.read(ROOT / "integrations/cursor/bootstrap.py")
    record = {
        "format": 1,
        "workspace": str(workspace),
        "source": str(control / boot.PLUGIN),
        "runtime": str(runtime),
        "python": str(python),
        "archive_sha256": checksum.lower(),
        "sources": {name: boot.digest(data) for name, data in files.items()},
        "bootstrap_sha256": boot.digest(bootstrap),
        "helper_sha256": boot.digest(boot.read(Path(__file__).resolve())),
        "config_before_sha256": boot.digest(raw) if raw is not None else None,
        "structure": {
            "cursor_created": not (workspace / ".cursor").exists(),
            "config_created": raw is None,
            "version_created": "version" not in current,
            "hooks_created": "hooks" not in current,
            "event_created": "workspaceOpen" not in current.get("hooks", {}),
        },
    }
    ledger = encoded(record)
    owned = boot.command(workspace, str(python), boot.digest(ledger))
    changed = json.loads(json.dumps(current))
    changed.setdefault("version", 1)
    changed.setdefault("hooks", {}).setdefault("workspaceOpen", []).append(owned)
    return record, files, ledger, changed, raw, mode


def plan(
    workspace: Path, archive: Path, checksum: str, python: Path, runtime: Path
) -> dict[str, Any]:
    record, files, ledger, changed, raw, _ = _prepare(workspace, archive, checksum, python, runtime)
    workspace = Path(record["workspace"])
    control = workspace / boot.CONTROL
    owned = boot.command(workspace, record["python"], boot.digest(ledger))
    creates = [
        {"path": str(control / boot.PLUGIN / name), "sha256": boot.digest(data)}
        for name, data in sorted(files.items())
    ]
    creates += [
        {"path": str(control / boot.BOOTSTRAP), "sha256": record["bootstrap_sha256"]},
        {"path": str(control / boot.STATE), "sha256": boot.digest(ledger)},
    ]
    return {
        "status": "planned",
        "activation": "not_performed",
        "files": creates,
        "config_delta": {
            "path": str(workspace / ".cursor/hooks.json"),
            "before_sha256": boot.digest(raw) if raw is not None else None,
            "after_sha256": boot.digest(encoded(changed)),
            "added_entry": {"event": "workspaceOpen", "definition": owned},
            "existing_event_count": len(changed["hooks"])
            - int(record["structure"]["event_created"]),
            "existing_workspaceOpen_count": len(changed["hooks"]["workspaceOpen"]) - 1,
        },
        "runtime_action": "not_modified",
    }


def _parent_fd(file: Path) -> int:
    """Walk from / using anchored directory descriptors, never following links."""
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in file.parent.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError:
        os.close(descriptor)
        raise


def _read_at(directory: int, name: str, limit: int) -> tuple[bytes, os.stat_result]:
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise boot.StateError("nonregular_owned_file")
        content = handle.read(limit + 1)
    if len(content) > limit:
        raise boot.StateError("owned_file_size_limit")
    return content, info


def _write_owned_tree(control: Path, files: dict[str, bytes]) -> None:
    """Create fresh owned files below anchored, no-follow directories."""
    parent = _parent_fd(control)
    root = -1
    try:
        os.mkdir(control.name, mode=0o700, dir_fd=parent)
        root = os.open(control.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
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


def _atomic_config(workspace: Path, data: bytes | None, before: bytes | None, mode: int) -> None:
    _, current, current_mode = boot.config(workspace)
    if current != before or current_mode != mode:
        raise boot.StateError("config_changed_concurrently")
    file = workspace / ".cursor/hooks.json"
    file.parent.mkdir(exist_ok=True)
    directory = _parent_fd(file)
    temporary = ".guardtrellis-" + secrets.token_hex(12)
    try:
        boot.path(file)
        if data is not None:
            descriptor = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode,
                dir_fd=directory,
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
                os.fchmod(handle.fileno(), mode)
        try:
            current, info = _read_at(directory, file.name, boot.LIMIT)
            current_mode = stat.S_IMODE(info.st_mode)
        except FileNotFoundError:
            current, current_mode = None, 0o600
        if current != before or current_mode != mode:
            raise boot.StateError("config_changed_concurrently")
        if data is None:
            os.unlink(file.name, dir_fd=directory)
        else:
            os.replace(temporary, file.name, src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass
        os.close(directory)


def _delete_control(workspace: Path, record: dict[str, Any], ledger_sha256: str) -> None:
    control = workspace / boot.CONTROL
    expected = {
        boot.STATE: ledger_sha256,
        boot.BOOTSTRAP: record["bootstrap_sha256"],
        **{boot.PLUGIN + "/" + name: value for name, value in record["sources"].items()},
    }
    for name, checksum in expected.items():
        file = control / name
        if file.exists():
            if boot.digest(boot.read(file, boot.SOURCE_LIMIT)) != checksum:
                raise boot.StateError("owned_file_changed_during_removal")
    # Validate the entire tree immediately before any deletion, including additions.
    allowed_dirs = {
        parent.as_posix()
        for name in (*expected, boot.STATE)
        for parent in Path(name).parents
        if parent != Path(".")
    }
    actual = list(control.rglob("*"))
    for file in actual:
        relative = file.relative_to(control).as_posix()
        boot.path(file)
        if file.is_dir():
            if relative not in allowed_dirs:
                raise boot.StateError("unknown_owned_directory")
        elif relative not in expected and relative != boot.STATE:
            raise boot.StateError("unknown_owned_file")
    for file in sorted(actual, key=lambda value: len(value.parts), reverse=True):
        if file == control / boot.STATE:
            continue
        boot.path(file)
        directory = _parent_fd(file)
        try:
            info = os.stat(file.name, dir_fd=directory, follow_symlinks=False)
            relative = file.relative_to(control).as_posix()
            if relative in allowed_dirs and stat.S_ISDIR(info.st_mode):
                os.rmdir(file.name, dir_fd=directory)
            elif relative in expected and stat.S_ISREG(info.st_mode):
                content, read_info = _read_at(directory, file.name, boot.SOURCE_LIMIT)
                if boot.digest(content) != expected[relative] or info.st_ino != read_info.st_ino:
                    raise boot.StateError("owned_file_changed_during_removal")
                os.unlink(file.name, dir_fd=directory)
            else:
                raise boot.StateError("owned_file_type_changed")
        finally:
            os.close(directory)
    directory = _parent_fd(control / boot.STATE)
    try:
        content, _ = _read_at(directory, boot.STATE, boot.LIMIT)
        if boot.digest(content) != ledger_sha256:
            raise boot.StateError("ledger_changed_during_removal")
        os.unlink(boot.STATE, dir_fd=directory)
    finally:
        os.close(directory)
    directory = _parent_fd(control)
    try:
        os.rmdir(control.name, dir_fd=directory)
    finally:
        os.close(directory)


def remove(workspace: Path) -> dict[str, Any]:
    workspace = _workspace(workspace)
    record, current, raw, mode, present = boot.inspect(workspace, incomplete=True)
    ledger_sha256 = boot.digest(boot.read(workspace / boot.CONTROL / boot.STATE))
    if present:
        owned = boot.command(
            workspace,
            record["python"],
            boot.digest(boot.read(workspace / boot.CONTROL / boot.STATE)),
        )
        changed = json.loads(json.dumps(current))
        changed["hooks"]["workspaceOpen"].remove(owned)
        flags = record["structure"]
        if not changed["hooks"]["workspaceOpen"] and flags["event_created"]:
            del changed["hooks"]["workspaceOpen"]
        if not changed["hooks"] and flags["hooks_created"]:
            del changed["hooks"]
        if flags["version_created"] and set(changed) == {"version"}:
            del changed["version"]
        data = None if flags["config_created"] and not changed else encoded(changed)
        boot.inspect(workspace, incomplete=True)
        _atomic_config(workspace, data, raw, mode)
    _delete_control(workspace, record, ledger_sha256)
    if record["structure"]["cursor_created"]:
        try:
            directory = _parent_fd(workspace / ".cursor")
            try:
                os.rmdir(".cursor", dir_fd=directory)
            finally:
                os.close(directory)
        except OSError:
            pass
    return {
        "status": "configuration_removed",
        "native_unload": "not_observed",
        "process_restart_required": True,
        "runtime_action": "not_modified",
    }


def install(
    workspace: Path, archive: Path, checksum: str, python: Path, runtime: Path
) -> dict[str, Any]:
    record, files, ledger, changed, raw, mode = _prepare(
        workspace, archive, checksum, python, runtime
    )
    workspace = Path(record["workspace"])
    control = workspace / boot.CONTROL
    try:
        contents = {
            boot.STATE: ledger,
            boot.BOOTSTRAP: boot.read(ROOT / "integrations/cursor/bootstrap.py"),
            **{boot.PLUGIN + "/" + name: data for name, data in files.items()},
        }
        _write_owned_tree(control, contents)
        boot.inspect(workspace, incomplete=True)
        _atomic_config(workspace, encoded(changed), raw, mode)
        boot.inspect(workspace)
    except (OSError, ValueError, TypeError, boot.StateError, release.ReleaseError):
        try:
            remove(workspace)
        except (OSError, ValueError, TypeError, boot.StateError):
            if control.exists() and not any(control.iterdir()):
                control.rmdir()
        raise boot.StateError("installation_failed_review_owned_state") from None
    return {
        "status": "configuration_staged",
        "activation": "not_performed",
        "source": record["source"],
        "runtime_action": "not_modified",
    }


def health(workspace: Path, check_runtime: bool = False) -> dict[str, Any]:
    workspace = _workspace(workspace)
    record, _, _, _, _ = boot.inspect(workspace)
    runtime_check: dict[str, str] = {"status": "not_requested"}
    if check_runtime:
        env = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "UV_PROJECT", "UV_PROJECT_ENVIRONMENT"):
            env.pop(key, None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            checked = subprocess.run(
                [
                    record["python"],
                    "-I",
                    "-B",
                    str(Path(record["source"]) / "scripts/runtime_setup.py"),
                    "doctor",
                    "--dest",
                    record["runtime"],
                ],
                capture_output=True,
                env=env,
                timeout=30,
                check=False,
            )
            report = boot.parse(checked.stdout)
            passed = (
                checked.returncode == 0
                and report.get("status") == "local_checks_ready"
                and report.get("sdk_version") == "0.1.9"
            )
        except (OSError, subprocess.TimeoutExpired, boot.StateError):
            passed = False
        runtime_check["status"] = "local_checks_ready" if passed else "unavailable"
        boot.inspect(workspace)
    return {
        "status": "configuration_ready",
        "native_activation": "not_observed",
        "runtime_check": runtime_check,
        "runtime_handoff": {
            "path": record["runtime"],
            "environment_variable": "GUARDTRELLIS_CURSOR_RUNTIME",
            "gui_environment": "not_observed",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "install", "health", "remove"):
        command_parser = commands.add_parser(name)
        command_parser.add_argument("--workspace", type=Path, required=True)
        if name in ("plan", "install"):
            command_parser.add_argument("--archive", type=Path, required=True)
            command_parser.add_argument("--sha256", required=True)
            command_parser.add_argument("--python", type=Path, default=Path(sys.executable))
            command_parser.add_argument("--runtime", type=Path, required=True)
        if name == "health":
            command_parser.add_argument("--check-runtime", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command in ("plan", "install"):
            result = (plan if args.command == "plan" else install)(
                args.workspace, args.archive, args.sha256, args.python, args.runtime
            )
        elif args.command == "health":
            result = health(args.workspace, args.check_runtime)
        else:
            result = remove(args.workspace)
    except (
        boot.StateError,
        release.ReleaseError,
        OSError,
        ValueError,
        TypeError,
        RecursionError,
    ) as error:
        reason = "invalid_owned_state"
        if isinstance(error, boot.StateError):
            candidate = str(error)
            reason = (
                candidate if re.fullmatch(r"[a-z_]+", candidate) else "owned_workspace_check_failed"
            )
        elif isinstance(error, release.ReleaseError):
            reason = "native_archive_check_failed"
        elif isinstance(error, OSError):
            reason = "filesystem_check_failed"
        print(
            json.dumps({"status": "unavailable", "reason": reason, "activation": "not_performed"}),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    if (
        args.command == "health"
        and args.check_runtime
        and result["runtime_check"]["status"] != "local_checks_ready"
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
