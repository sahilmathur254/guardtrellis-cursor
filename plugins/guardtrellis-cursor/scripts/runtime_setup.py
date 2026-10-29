"""Explicit terminal-only runtime lifecycle; never installs or activates a plugin."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

TAG = "0.1.0-preview.1-sdk0.1.9"
SDK = "0.1.9"
MARKER = ".guardtrellis-cursor-runtime-v1"
RECORD = ".guardtrellis-cursor-runtime.json"
MAX_RECORD = 8 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "adapters/common/__init__.py",
    "adapters/common/prompt_runtime.py",
    "adapters/codex/redact_prompt.py",
    "adapters/cursor/prompt_check.py",
    "adapters/cursor/prepare_prompt.py",
    "runtime/pyproject.toml",
    "runtime/uv.lock",
)


class RuntimeErrorSafe(Exception):
    """A static, non-sensitive lifecycle failure."""


def default_destination() -> Path:
    configured = os.environ.get("GUARDTRELLIS_CURSOR_RUNTIME")
    return (
        Path(configured)
        if configured is not None
        else Path.home() / "Library/Application Support/GuardTrellis/Cursor" / TAG
    )


def destination(value: Path, plugin: Path) -> Path:
    value = value.expanduser()
    if not value.is_absolute() or value.is_symlink():
        raise RuntimeErrorSafe("Runtime destination must be an absolute, non-symlink path.")
    root = value.resolve()
    plugin = plugin.resolve()
    prohibited = [
        Path.home(),
        *(Path.home() / name for name in (".codex", ".claude", ".cursor")),
        Path.home() / "Library/Application Support/Cursor",
    ]
    if root == Path.home().resolve() or any(
        root.is_relative_to(path.resolve()) for path in prohibited[1:]
    ):
        raise RuntimeErrorSafe("Runtime destination cannot be a normal agent profile.")
    if root.is_relative_to(plugin) or plugin.is_relative_to(root):
        raise RuntimeErrorSafe("Runtime destination must be outside the plugin directory.")
    return root


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_map(plugin: Path) -> dict[str, str]:
    result = {}
    for name in SOURCES:
        path = plugin / name
        if not path.is_file() or any(
            entry.is_symlink() for entry in (path, *path.parents) if entry != plugin
        ):
            raise RuntimeErrorSafe("Bundled runtime sources are missing or linked.")
        result[name] = digest(path.read_bytes())
    try:
        project = tomllib.loads((plugin / "runtime/pyproject.toml").read_text())
        lock = tomllib.loads((plugin / "runtime/uv.lock").read_text())
        dependencies = project["project"]["dependencies"]
        sdk = [
            item
            for item in lock["package"]
            if isinstance(item, dict) and item.get("name") == "guardtrellis"
        ]
        if dependencies != [f"guardtrellis=={SDK}"] or len(sdk) != 1 or sdk[0]["version"] != SDK:
            raise ValueError
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise RuntimeErrorSafe("Bundled SDK metadata does not match the supported pin.") from None
    return result


def fingerprint(path: Path) -> dict[str, Any]:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return {"kind": "symlink", "target": os.readlink(path)}
    if stat.S_ISREG(mode):
        return {"kind": "file", "sha256": digest(path.read_bytes()), "mode": stat.S_IMODE(mode)}
    if stat.S_ISDIR(mode):
        return {"kind": "directory", "mode": stat.S_IMODE(mode)}
    raise RuntimeErrorSafe("Runtime contains an unsupported filesystem entry.")


def inventory(root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted((*dirs, *files)):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if relative == RECORD:
                continue
            result[relative] = fingerprint(path)
        dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
    return result


def save_record(root: Path, sources: dict[str, str], status: str) -> None:
    record = {
        "format": 1,
        "tag": TAG,
        "root": str(root),
        "status": status,
        "sources": sources,
        "entries": inventory(root),
    }
    path = root / RECORD
    if path.is_symlink():
        raise RuntimeErrorSafe("Runtime ownership record is linked.")
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")


def load_record(root: Path) -> dict[str, Any]:
    path = root / RECORD
    if root.is_symlink() or path.is_symlink() or not path.is_file():
        raise RuntimeErrorSafe("Runtime has no regular ownership record.")
    if path.stat().st_size > MAX_RECORD:
        raise RuntimeErrorSafe("Runtime ownership record is too large.")
    try:
        record = json.loads(path.read_bytes())
    except (ValueError, UnicodeError, RecursionError):
        raise RuntimeErrorSafe("Runtime ownership record is invalid.") from None
    if (
        not isinstance(record, dict)
        or record.get("format") != 1
        or record.get("tag") != TAG
        or record.get("root") != str(root)
        or record.get("status") not in ("ready", "incomplete")
        or not isinstance(record.get("entries"), dict)
        or not isinstance(record.get("sources"), dict)
    ):
        raise RuntimeErrorSafe("Runtime ownership record does not match this destination.")
    # Comparing against a fresh inventory rejects traversal keys, invented kinds,
    # symlink-directory substitutions, changed files and unrecorded additions.
    if record["entries"] != inventory(root):
        raise RuntimeErrorSafe("Runtime changed; inspect it before removal or use.")
    return record


def environment() -> dict[str, str]:
    env = os.environ.copy()
    for name in ("UV_PROJECT", "UV_PROJECT_ENVIRONMENT", "PYTHONPATH", "PYTHONHOME"):
        env.pop(name, None)
    env.update(UV_PYTHON_DOWNLOADS="never", PYTHONDONTWRITEBYTECODE="1", UV_NO_PROGRESS="1")
    return env


def runtime_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run_local(
    command: list[str], *, data: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            command, input=data, capture_output=True, env=environment(), timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeErrorSafe("Runtime local check could not execute.") from None


def health(root: Path, plugin: Path) -> None:
    python = runtime_python(root)
    if not python.is_file() or not os.access(python, os.X_OK):
        raise RuntimeErrorSafe("Runtime Python is unavailable.")
    version = run_local(
        [
            str(python),
            "-I",
            "-B",
            "-c",
            "import importlib.metadata; print(importlib.metadata.version('guardtrellis'))",
        ]
    )
    if version.returncode or version.stdout != (SDK + "\n").encode() or version.stderr:
        raise RuntimeErrorSafe("Runtime SDK version check failed.")
    script = str(plugin / "adapters/cursor/prompt_check.py")
    for prompt, continuing in (("Explain sorting.", True), ("ghp_" + "a" * 36, False)):
        checked = run_local(
            [
                str(python),
                "-I",
                "-B",
                script,
                "--profile",
                "enforce-secrets-v1",
                "--diagnostics",
                "findings",
            ],
            data=json.dumps({"hook_event_name": "beforeSubmitPrompt", "prompt": prompt}).encode(),
        )
        try:
            response = json.loads(checked.stdout)
            report = json.loads(checked.stderr) if not continuing else None
        except (ValueError, UnicodeError):
            raise RuntimeErrorSafe("Runtime synthetic prompt check failed.") from None
        expected: dict[str, object] = {"continue": continuing}
        if not continuing:
            expected["user_message"] = (
                "GuardTrellis detected a recognized secret pattern. Remove it and resubmit."
            )
        if checked.returncode or response != expected or response.get("continue") is not continuing:
            raise RuntimeErrorSafe("Runtime synthetic prompt check failed.")
        expected_report = {
            "contract": "cursor_prompt_v1",
            "profile": "enforce-secrets-v1",
            "boundary": "beforeSubmitPrompt.prompt",
            "check_status": "checked",
            "policy_action": "block",
            "scanner_action": "block",
            "reason_code": "secret_detected",
            "finding_codes": ["secret_github_classic"],
            "sdk_version": SDK,
            "requested_continue": False,
            "host_enforcement": "not_observed",
        }
        if (continuing and checked.stderr) or (not continuing and report != expected_report):
            raise RuntimeErrorSafe("Runtime synthetic prompt check failed.")
    preview = run_local(
        [str(python), "-I", "-B", str(plugin / "adapters/cursor/prepare_prompt.py")],
        data=b"Mira mira@example.org +14155550123",
    )
    try:
        report = json.loads(preview.stderr)
    except (ValueError, UnicodeError):
        raise RuntimeErrorSafe("Runtime synthetic masking check failed.") from None
    expected_preview = {
        "contract": "cursor_reviewed_prefill_v1",
        "boundary": "local_reviewed_prefill",
        "check_status": "checked",
        "scanner_action": "redact",
        "reason_code": "pii_redacted",
        "finding_codes": ["pii_email", "pii_phone"],
        "pii_formats": ["email", "phone"],
        "sdk_version": SDK,
        "prefill_status": "not_requested",
        "submission": "not_performed",
    }
    if preview.returncode or preview.stdout != b"Mira [PII] [PII]" or report != expected_preview:
        raise RuntimeErrorSafe("Runtime synthetic masking check failed.")


def setup(root: Path, plugin: Path, python: Path, uv: str = "uv") -> dict[str, Any]:
    root = destination(root, plugin)
    if root.exists() or root.is_symlink():
        raise RuntimeErrorSafe("Setup requires a fresh runtime destination.")
    sources = source_map(plugin)
    tool = shutil.which(uv)
    if tool is None:
        raise RuntimeErrorSafe("uv must already be installed; no destination was created.")
    python = python.expanduser()
    if not python.is_absolute() or not python.is_file() or not os.access(python, os.X_OK):
        raise RuntimeErrorSafe("Select an existing absolute Python executable.")
    version = run_local(
        [
            str(python),
            "-I",
            "-B",
            "-c",
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
        ]
    )
    if version.returncode or version.stdout not in (b"3.11\n", b"3.12\n", b"3.13\n", b"3.14\n"):
        raise RuntimeErrorSafe("Python 3.11 through 3.14 is required.")
    root.mkdir(parents=True)
    save_record(root, sources, "incomplete")
    env = environment()
    env["UV_PROJECT_ENVIRONMENT"] = str(root)
    try:
        initialized = subprocess.run(
            [
                tool,
                "--no-config",
                "venv",
                "--no-project",
                "--allow-existing",
                "--python",
                str(python),
                str(root),
            ],
            cwd=plugin / "runtime",
            env=env,
            capture_output=True,
            timeout=180,
            check=False,
        )
        if initialized.returncode:
            raise RuntimeErrorSafe("Runtime initialization failed.")
        completed = subprocess.run(
            [
                tool,
                "--no-config",
                "sync",
                "--project",
                str(plugin / "runtime"),
                "--locked",
                "--no-dev",
                "--no-install-project",
                "--python",
                str(python),
            ],
            cwd=plugin / "runtime",
            env=env,
            capture_output=True,
            timeout=180,
            check=False,
        )
        if completed.returncode:
            raise RuntimeErrorSafe(
                "Runtime setup failed; inspect or remove the recorded partial runtime."
            )
        installed = inventory(root)
        health(root, plugin)
        if source_map(plugin) != sources or inventory(root) != installed:
            raise RuntimeErrorSafe("Runtime or bundled sources changed during setup checks.")
        (root / MARKER).write_text(TAG + "\n")
        save_record(root, sources, "ready")
    except (OSError, subprocess.TimeoutExpired, RuntimeErrorSafe):
        marker = root / MARKER
        if marker.is_file() and not marker.is_symlink():
            marker.unlink()
        save_record(root, sources, "incomplete")
        raise RuntimeErrorSafe(
            "Runtime setup failed; inspect or remove the recorded partial runtime."
        ) from None
    return {
        "status": "ready",
        "runtime": str(root),
        "sdk_version": SDK,
        "hook_activation": "not_performed",
    }


def doctor(root: Path, plugin: Path) -> dict[str, Any]:
    root = destination(root, plugin)
    record = load_record(root)
    if record["status"] != "ready" or record["sources"] != source_map(plugin):
        raise RuntimeErrorSafe("Runtime is incomplete or belongs to different bundled sources.")
    marker = root / MARKER
    if (
        marker.is_symlink()
        or not marker.is_file()
        or marker.read_bytes() not in (TAG.encode(), (TAG + "\n").encode())
    ):
        raise RuntimeErrorSafe("Runtime ready marker is invalid.")
    health(root, plugin)
    if load_record(root) != record or source_map(plugin) != record["sources"]:
        raise RuntimeErrorSafe("Runtime or bundled sources changed during local checks.")
    return {
        "status": "local_checks_ready",
        "sdk_version": SDK,
        "runtime": str(root),
        "hook_configuration": "not_inspected",
        "host_enforcement": "not_observed",
    }


def remove(root: Path, plugin: Path) -> dict[str, Any]:
    root = destination(root, plugin)
    record = load_record(root)
    for name, expected in sorted(
        record["entries"].items(), key=lambda item: len(Path(item[0]).parts), reverse=True
    ):
        path = root / name
        if any(parent.is_symlink() for parent in path.parents if parent != root):
            raise RuntimeErrorSafe("Runtime path became linked; removal stopped.")
        if fingerprint(path) != expected:
            raise RuntimeErrorSafe("Runtime changed during removal; removal stopped.")
        if expected["kind"] == "directory":
            path.rmdir()
        else:
            path.unlink()
    (root / RECORD).unlink()
    root.rmdir()
    return {"status": "removed", "runtime": str(root), "plugin_and_profiles": "unchanged"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("setup", "doctor", "remove"):
        command = commands.add_parser(name)
        command.add_argument("--dest", type=Path, default=default_destination())
        if name == "setup":
            command.add_argument("--python", type=Path, default=Path(sys.executable))
            command.add_argument("--uv", default="uv")
    args = parser.parse_args(argv)
    try:
        if args.command == "setup":
            result = setup(args.dest, ROOT, args.python, args.uv)
        elif args.command == "doctor":
            result = doctor(args.dest, ROOT)
        else:
            result = remove(args.dest, ROOT)
    except (RuntimeErrorSafe, OSError):
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "reason": "runtime_lifecycle_check_failed",
                    "hook_activation": "not_performed",
                }
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
