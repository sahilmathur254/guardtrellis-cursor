"""Owned project bootstrap: fixed plugin paths, bounded input and no SDK execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

CONTROL = ".guardtrellis-cursor"
STATE = "installation.json"
BOOTSTRAP = "bootstrap.py"
PLUGIN = "guardtrellis-cursor"
LIMIT = 65_536
SOURCE_LIMIT = 16 * 1024 * 1024
PLUGIN_FILES = frozenset(
    (
        ".cursor-plugin/plugin.json",
        "COMPATIBILITY.md",
        "LICENSE",
        "NOTICE",
        "PRIVACY.md",
        "README.md",
        "SUPPORT.md",
        "adapters/codex/redact_prompt.py",
        "adapters/common/__init__.py",
        "adapters/common/prompt_runtime.py",
        "adapters/cursor/prepare_prompt.py",
        "adapters/cursor/prompt_check.py",
        "assets/logo.svg",
        "commands/guardtrellis-health.md",
        "commands/guardtrellis-prepare.md",
        "commands/guardtrellis-remove.md",
        "commands/guardtrellis-setup.md",
        "hooks/hooks.json",
        "runtime/pyproject.toml",
        "runtime/uv.lock",
        "scripts/guardtrellis.sh",
        "scripts/runtime_setup.py",
        "SOURCE-MANIFEST.json",
    )
)


class StateError(Exception):
    """Static reason codes only; never include configuration values."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse(data: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    try:
        if len(data) > LIMIT:
            raise ValueError
        result = json.loads(
            data,
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
        if not isinstance(result, dict):
            raise ValueError
        return result
    except (ValueError, UnicodeError, RecursionError):
        raise StateError("invalid_json") from None


def path(value: str | Path) -> Path:
    result = Path(value)
    if not result.is_absolute() or any(ord(char) < 32 for char in str(result)):
        raise StateError("unsafe_path")
    if any(part.is_symlink() for part in (result, *result.parents)) or result != result.resolve():
        raise StateError("linked_or_aliased_path")
    return result


def protected(value: Path) -> bool:
    home = Path.home().resolve()
    roots = [home / name for name in (".codex", ".claude", ".cursor")]
    roots.append(home / "Library/Application Support/Cursor")
    return value == home or value == Path("/") or any(value.is_relative_to(root) for root in roots)


def read(file: Path, limit: int = LIMIT) -> bytes:
    path(file)
    if not stat.S_ISREG(file.lstat().st_mode):
        raise StateError("nonregular_file")
    with file.open("rb") as handle:
        result = handle.read(limit + 1)
    if len(result) > limit:
        raise StateError("size_limit")
    return result


def config(workspace: Path) -> tuple[dict[str, Any], bytes | None, int]:
    file = workspace / ".cursor/hooks.json"
    path(file)
    if file.parent.exists() and not file.parent.is_dir():
        raise StateError("invalid_config_directory")
    if not file.exists():
        return {}, None, 0o600
    raw = read(file)
    result = parse(raw)
    if "version" in result and (type(result["version"]) is not int or result["version"] != 1):
        raise StateError("unsupported_config_version")
    hooks = result.get("hooks", {})
    if not isinstance(hooks, dict):
        raise StateError("invalid_hooks")
    for entries in hooks.values():
        if not isinstance(entries, list):
            raise StateError("invalid_hooks")
        for entry in entries:
            if not isinstance(entry, dict):
                raise StateError("invalid_hooks")
            kind = entry.get("type", "command")
            field = "command" if kind == "command" else "prompt" if kind == "prompt" else None
            if field is None or not isinstance(entry.get(field), str) or not entry[field]:
                raise StateError("unsupported_hook_entry")
    return result, raw, stat.S_IMODE(file.stat().st_mode)


def command(workspace: Path, python: str, checksum: str) -> dict[str, Any]:
    return {
        "type": "command",
        "command": shlex.join(
            [
                python,
                "-I",
                "-B",
                str(workspace / CONTROL / BOOTSTRAP),
                "--state",
                str(workspace / CONTROL / STATE),
                "--sha256",
                checksum,
            ]
        ),
        "timeout": 5,
    }


def inspect(
    workspace: Path, *, incomplete: bool = False, expected: str | None = None
) -> tuple[dict[str, Any], dict[str, Any], bytes | None, int, bool]:
    workspace = path(workspace)
    if protected(workspace) or not workspace.is_dir():
        raise StateError("unsafe_workspace")
    control = workspace / CONTROL
    raw = read(control / STATE)
    if expected is not None and digest(raw) != expected:
        raise StateError("ledger_changed")
    record = parse(raw)
    required = {
        "format",
        "workspace",
        "source",
        "runtime",
        "python",
        "archive_sha256",
        "sources",
        "bootstrap_sha256",
        "helper_sha256",
        "config_before_sha256",
        "structure",
    }
    if set(record) != required or type(record.get("format")) is not int or record["format"] != 1:
        raise StateError("unknown_ledger")
    if record["workspace"] != str(workspace) or record["source"] != str(control / PLUGIN):
        raise StateError("ledger_paths_changed")
    runtime = path(record["runtime"])
    python = path(record["python"])
    if protected(runtime) or runtime.is_relative_to(workspace) or workspace.is_relative_to(runtime):
        raise StateError("unsafe_runtime")
    if not python.is_file() or not os.access(python, os.X_OK):
        raise StateError("bootstrap_python_unavailable")
    if not isinstance(record["sources"], dict) or set(record["sources"]) != PLUGIN_FILES:
        raise StateError("unknown_source_inventory")
    hashes = [record[key] for key in ("archive_sha256", "bootstrap_sha256", "helper_sha256")]
    hashes += list(record["sources"].values())
    if not all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes):
        raise StateError("invalid_hash_inventory")
    if record["config_before_sha256"] is not None and not (
        isinstance(record["config_before_sha256"], str)
        and re.fullmatch(r"[0-9a-f]{64}", record["config_before_sha256"])
    ):
        raise StateError("invalid_config_ownership")
    flags = record["structure"]
    if (
        not isinstance(flags, dict)
        or set(flags)
        != {"cursor_created", "config_created", "version_created", "hooks_created", "event_created"}
        or not all(type(value) is bool for value in flags.values())
    ):
        raise StateError("invalid_structure_ownership")
    expected_files = {
        STATE: digest(raw),
        BOOTSTRAP: record["bootstrap_sha256"],
        **{PLUGIN + "/" + name: value for name, value in record["sources"].items()},
    }
    directories = {
        parent.as_posix()
        for name in expected_files
        for parent in PurePosixPath(name).parents
        if parent != PurePosixPath(".")
    }
    found = set()
    pending = [control]
    total = 0
    while pending:
        directory = pending.pop()
        path(directory)
        for child in directory.iterdir():
            name = child.relative_to(control).as_posix()
            if child.is_symlink():
                raise StateError("linked_owned_state")
            if child.is_dir():
                if name not in directories:
                    raise StateError("unknown_owned_directory")
                pending.append(child)
            elif child.is_file() and name in expected_files:
                content = read(child, SOURCE_LIMIT)
                total += len(content)
                if total > SOURCE_LIMIT or digest(content) != expected_files[name]:
                    raise StateError("owned_file_changed")
                found.add(name)
            else:
                raise StateError("unknown_owned_file")
    if not incomplete and found != set(expected_files):
        raise StateError("owned_file_missing")
    current, config_raw, mode = config(workspace)
    owned = command(workspace, str(python), digest(raw))
    entries = current.get("hooks", {}).get("workspaceOpen", [])
    matches = sum(entry == owned for entry in entries)
    references = sum(
        isinstance(entry.get("command"), str) and str(control / BOOTSTRAP) in entry["command"]
        for values in current.get("hooks", {}).values()
        for entry in values
    )
    if matches != 1 or references != 1:
        unchanged = (digest(config_raw) if config_raw is not None else None) == record[
            "config_before_sha256"
        ]
        if not (incomplete and matches == references == 0 and unchanged):
            raise StateError("owned_entry_changed_or_ambiguous")
    return record, current, config_raw, mode, matches == 1


def handle(raw: bytes, state: Path, checksum: str) -> dict[str, list[str]]:
    event = parse(raw)
    if event.get("hook_event_name") != "workspaceOpen":
        raise StateError("unsupported_event")
    state = path(state)
    if state.name != STATE or state.parent.name != CONTROL:
        raise StateError("invalid_state_path")
    workspace = state.parent.parent
    if event.get("workspace_roots") != [str(workspace)]:
        raise StateError("workspace_mismatch")
    record, _, _, _, _ = inspect(workspace, expected=checksum)
    return {"pluginPaths": [record["source"]]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    try:
        result = handle(sys.stdin.buffer.read(LIMIT + 1), args.state, args.sha256)
    except (StateError, OSError, ValueError, TypeError, RecursionError):
        print('{"pluginPaths":[]}')
        print(
            '{"component":"guardtrellis_workspace_bootstrap","status":"unavailable","reason":"owned_workspace_check_failed"}',
            file=sys.stderr,
        )
        return 0
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
