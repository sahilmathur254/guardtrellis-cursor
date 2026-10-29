"""Verify native Cursor sources offline in disposable roots; never activate a host."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PHASES = ("tests", "static", "artifacts", "lifecycle")
SDK = "0.1.9"
UV_VERSION = "0.8.17"
CONFIG = "plugins/guardtrellis/adapters/codex/pyproject.toml"
TOOL_FILES = (
    "scripts/cursor_release.py",
    "scripts/check_cursor_release.py",
    "scripts/cursor_workspace.py",
    "integrations/cursor/bootstrap.py",
    "integrations/cursor/plugin/scripts/runtime_setup.py",
    "scripts/cursor_delivery.py",
)
TEST_FILES = (
    "tests/test_cursor_release.py",
    "tests/test_check_cursor_release.py",
    "integrations/cursor/tests/test_launcher.py",
    "integrations/cursor/tests/test_runtime_setup.py",
    "tests/test_cursor_workspace.py",
    "tests/test_cursor_delivery.py",
    "tests/test_cursor_public_copy.py",
)


class CheckFailure(Exception):
    """A static stage failure; child output may contain fixtures and stays captured."""


def emit(**record: object) -> None:
    print(json.dumps(record, sort_keys=True), flush=True)


def builder_module(source: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "guardtrellis_native_cursor_builder", source / "scripts/cursor_release.py"
    )
    if spec is None or spec.loader is None:
        raise CheckFailure("native_builder_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def delivery_module(source: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "guardtrellis_cursor_delivery", source / "scripts/cursor_delivery.py"
    )
    if spec is None or spec.loader is None:
        raise CheckFailure("delivery_builder_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment(work: Path, *, cache: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("UV_PROJECT", "UV_PROJECT_ENVIRONMENT", "PYTHONHOME", "PYTHONPATH"):
        env.pop(key, None)
    env.update(
        UV_PYTHON_DOWNLOADS="never",
        PYTHONDONTWRITEBYTECODE="1",
        UV_NO_PROGRESS="1",
        MYPY_CACHE_DIR=str(work / "mypy-cache"),
    )
    if cache:
        destination = work / "uv-cache"
        seed = os.environ.get("UV_CACHE_DIR")
        if seed is not None:
            original = Path(seed)
            if not original.is_absolute() or not original.is_dir():
                raise CheckFailure("cache_source_unavailable")
            # Copy bytes, rather than hard links, so every uv write stays in this owned root.
            shutil.copytree(original, destination, symlinks=False)
        else:
            destination.mkdir()
        env["UV_CACHE_DIR"] = str(destination)
    return env


def run(
    label: str,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    data: bytes | None = None,
    timeout: int = 180,
    tests: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            input=data,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        emit(check=label, process="failed")
        raise CheckFailure("child_process_unavailable") from None
    if result.returncode:
        emit(check=label, process="failed", exit_code=result.returncode)
        raise CheckFailure("child_process_failed")
    if tests:
        matched = re.search(rb"\bRan (\d+) tests?\b", result.stderr)
        if matched is None or int(matched[1]) == 0:
            raise CheckFailure("test_discovery_empty")
        skipped_match = re.search(rb"\bskipped=(\d+)\b", result.stderr)
        skipped = int(skipped_match[1]) if skipped_match is not None else 0
        emit(
            check=label,
            process="failed" if skipped else "completed",
            tests=int(matched[1]),
            skipped=skipped,
        )
        if skipped:
            raise CheckFailure("native_tests_skipped")
    else:
        emit(check=label, process="completed")
    return result


def object_result(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise CheckFailure("child_metadata_invalid") from None
    if not isinstance(value, dict):
        raise CheckFailure("child_metadata_invalid")
    return cast(dict[str, Any], value)


def test_checks(source: Path, work: Path, uv: str) -> None:
    del uv
    env = environment(work)
    for label, relative in (
        ("native_builder_tests", TEST_FILES[0]),
        ("native_runner_tests", TEST_FILES[1]),
        ("native_launcher_tests", TEST_FILES[2]),
        ("native_runtime_setup_tests", TEST_FILES[3]),
        ("native_workspace_tests", TEST_FILES[4]),
        ("native_delivery_tests", TEST_FILES[5]),
        ("native_public_copy_tests", TEST_FILES[6]),
    ):
        path = source / relative
        if not path.is_file():
            raise CheckFailure("test_source_unavailable")
        run(
            label,
            [
                sys.executable,
                "-I",
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                str(path.parent),
                "-p",
                path.name,
                "-q",
            ],
            cwd=work,
            env=env,
            tests=True,
        )


def uv_executable(value: str, work: Path, env: dict[str, str]) -> str:
    executable = shutil.which(value)
    if executable is None:
        raise CheckFailure("uv_unavailable")
    result = run("uv_version", [executable, "--version"], cwd=work, env=env)
    if not re.fullmatch(rb"uv 0\.8\.17(?: [^\r\n]*)?\r?\n", result.stdout):
        raise CheckFailure("uv_version_mismatch")
    return executable


def static_checks(source: Path, work: Path, uv: str) -> None:
    env = environment(work, cache=True)
    executable = uv_executable(uv, work, env)
    project = work / "tool-project"
    project.mkdir()
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(source / "plugins/guardtrellis/adapters/codex" / name, project / name)
    env["UV_PROJECT_ENVIRONMENT"] = str(work / "tool-runtime")
    run(
        "locked_static_tools",
        [
            executable,
            "--no-config",
            "sync",
            "--locked",
            "--no-install-project",
            "--project",
            str(project),
            "--python",
            sys.executable,
        ],
        cwd=work,
        env=env,
    )
    binary = work / "tool-runtime/bin"
    targets = [str(source / path) for path in (*TOOL_FILES, *TEST_FILES)]
    config = str(source / CONFIG)
    for label, command in (
        ("ruff", [str(binary / "ruff"), "check", "--no-cache", "--config", config, *targets]),
        (
            "ruff_format",
            [str(binary / "ruff"), "format", "--check", "--no-cache", "--config", config, *targets],
        ),
        (
            "strict_mypy",
            [
                str(binary / "mypy"),
                "--strict",
                "--cache-dir",
                str(work / "mypy-cache"),
                "--config-file",
                config,
                *(str(source / path) for path in TOOL_FILES),
            ],
        ),
        (
            "shell_syntax",
            ["/bin/sh", "-n", str(source / "integrations/cursor/plugin/scripts/guardtrellis.sh")],
        ),
    ):
        run(label, command, cwd=work, env=env)


def artifact_checks(source: Path, work: Path, uv: str) -> None:
    del uv
    builder = builder_module(source)
    checked = builder.check_export(source, check_catalog=True)
    if checked.get("verified") is not True or checked.get("profile") != "advisory":
        raise CheckFailure("canonical_export_unverified")
    for profile in ("advisory", "enforce-secrets-v1"):
        first = builder.build(source, work / (profile + "-first"), profile)
        second = builder.build(source, work / (profile + "-second"), profile)
        if first["sha256"] != second["sha256"]:
            raise CheckFailure("native_build_not_reproducible")
        for built in (first, second):
            files = builder.verify(Path(built["archive"]), built["sha256"])
            record = object_result(files[builder.MANIFEST])
            if record.get("profile") != profile:
                raise CheckFailure("native_build_profile_mismatch")
        emit(check="native_artifact", profile=profile, sha256=first["sha256"], reproducible=True)
    emit(check="canonical_export", verified=True, profile="advisory", catalog="checked")


def workspace_checks(
    source: Path,
    work: Path,
    archive: Path,
    checksum: str,
    verified: dict[str, bytes],
    runtime: Path,
    env: dict[str, str],
) -> None:
    """Stage and remove configuration in an unopened fixture; never run its bootstrap."""
    workspace = work / "unopened owned workspace with spaces"
    workspace.mkdir()
    configuration = workspace / ".cursor/hooks.json"
    configuration.parent.mkdir()
    original = {"version": 1, "hooks": {"afterFileEdit": [{"command": "/usr/bin/true"}]}}
    configuration.write_text(json.dumps(original) + "\n")
    before = configuration.read_bytes()
    control = workspace / ".guardtrellis-cursor"
    ledger = runtime / ".guardtrellis-cursor-runtime.json"
    runtime_before = ledger.read_bytes()

    def cli(label: str, operation: str, *extra: str) -> dict[str, Any]:
        completed = run(
            label,
            [
                sys.executable,
                "-I",
                "-B",
                str(source / "scripts/cursor_workspace.py"),
                operation,
                "--workspace",
                str(workspace),
                *extra,
            ],
            cwd=work,
            env=env,
            timeout=30,
        )
        if completed.stderr:
            raise CheckFailure("workspace_helper_diagnostics_unexpected")
        return object_result(completed.stdout)

    selection = (
        "--archive",
        str(archive),
        "--sha256",
        checksum,
        "--python",
        sys.executable,
        "--runtime",
        str(runtime),
    )
    try:
        planned = cli("workspace_plan", "plan", *selection)
        if (
            planned.get("status") != "planned"
            or planned.get("activation") != "not_performed"
            or control.exists()
            or configuration.read_bytes() != before
        ):
            raise CheckFailure("workspace_plan_changed_configuration")
        installed = cli("workspace_install", "install", *selection)
        if (
            installed.get("status") != "configuration_staged"
            or installed.get("activation") != "not_performed"
            or installed.get("runtime_action") != "not_modified"
        ):
            raise CheckFailure("workspace_configuration_not_staged")
        plugin = control / "guardtrellis-cursor"
        paths = list(plugin.rglob("*"))
        after = {
            path.relative_to(plugin).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths
            if path.is_file()
        }
        if any(path.is_symlink() for path in paths) or after != {
            name: hashlib.sha256(data).hexdigest() for name, data in verified.items()
        }:
            raise CheckFailure("workspace_sources_do_not_match_archive")
        checked = cli("workspace_health", "health", "--check-runtime")
        runtime_check = checked.get("runtime_check")
        if (
            checked.get("status") != "configuration_ready"
            or checked.get("native_activation") != "not_observed"
            or not isinstance(runtime_check, dict)
            or runtime_check.get("status") != "local_checks_ready"
        ):
            raise CheckFailure("workspace_configuration_or_runtime_unavailable")
    finally:
        if control.exists():
            removed = cli("workspace_remove", "remove")
            if (
                removed.get("status") != "configuration_removed"
                or removed.get("native_unload") != "not_observed"
                or removed.get("process_restart_required") is not True
                or removed.get("runtime_action") != "not_modified"
                or control.exists()
            ):
                raise CheckFailure("workspace_removal_incomplete")
    if (
        object_result(configuration.read_bytes()) != original
        or ledger.read_bytes() != runtime_before
    ):
        raise CheckFailure("workspace_removal_changed_unrelated_configuration_or_runtime")
    emit(
        check="workspace_helper_lifecycle",
        status="passed",
        activation="not_performed",
        native_unload="not_observed",
        runtime_action="not_modified",
    )


def lifecycle_checks(source: Path, work: Path, uv: str) -> None:
    builder = builder_module(source)
    env = environment(work, cache=True)
    executable = uv_executable(uv, work, env)
    built = builder.build(source, work / "advisory-archive", "advisory")
    archive = Path(built["archive"])
    verified = builder.verify(archive, built["sha256"])
    plugin = work / "exact extracted plugin with spaces"
    builder.extract(archive, built["sha256"], plugin)
    runtime = work / "owned external runtime with spaces"
    env["GUARDTRELLIS_CURSOR_RUNTIME"] = str(runtime)

    def cli(label: str, operation: str, *extra: str) -> dict[str, Any]:
        completed = run(
            label,
            [
                sys.executable,
                "-I",
                "-B",
                str(plugin / "scripts/runtime_setup.py"),
                operation,
                "--dest",
                str(runtime),
                *extra,
            ],
            cwd=work,
            env=env,
            timeout=420,
        )
        if completed.stderr:
            raise CheckFailure("runtime_lifecycle_diagnostics_unexpected")
        return object_result(completed.stdout)

    try:
        installed = cli("runtime_setup", "setup", "--python", sys.executable, "--uv", executable)
        if installed.get("status") != "ready" or installed.get("sdk_version") != SDK:
            raise CheckFailure("runtime_setup_not_ready")
        checked = cli("runtime_doctor", "doctor")
        if (
            checked.get("status") != "local_checks_ready"
            or checked.get("sdk_version") != SDK
            or checked.get("host_enforcement") != "not_observed"
        ):
            raise CheckFailure("runtime_doctor_not_ready")
        workspace_checks(source, work, archive, built["sha256"], verified, runtime, env)
        delivery_checks(source, work, archive, built["sha256"], verified, runtime, env)
        launcher = plugin / "scripts/guardtrellis.sh"
        for profile, prompt, continuing in (
            ("advisory", "Explain sorting.", True),
            ("enforce-secrets-v1", "ghp_" + "a" * 36, False),
        ):
            response = run(
                "local_hook_" + profile,
                ["/bin/sh", str(launcher), "hook", "--profile", profile],
                cwd=work,
                env=env,
                data=json.dumps(
                    {"hook_event_name": "beforeSubmitPrompt", "prompt": prompt}
                ).encode(),
                timeout=10,
            )
            if object_result(response.stdout).get("continue") is not continuing:
                raise CheckFailure("local_hook_decision_mismatch")
            if continuing:
                if response.stderr:
                    raise CheckFailure("local_clean_hook_diagnostics_unexpected")
            else:
                report = object_result(response.stderr)
                if (
                    report.get("sdk_version") != SDK
                    or report.get("reason_code") != "secret_detected"
                    or report.get("host_enforcement") != "not_observed"
                ):
                    raise CheckFailure("local_secret_hook_metadata_mismatch")
        preview = run(
            "local_reviewed_prepare",
            ["/bin/sh", str(launcher), "prepare"],
            cwd=work,
            env=env,
            data=b"Mira mira@example.org +14155550123",
            timeout=10,
        )
        report = object_result(preview.stderr)
        if (
            preview.stdout != b"Mira [PII] [PII]"
            or report.get("sdk_version") != SDK
            or report.get("prefill_status") != "not_requested"
            or report.get("submission") != "not_performed"
        ):
            raise CheckFailure("local_reviewed_prepare_mismatch")
        moved = work / "moved plugin with spaces"
        plugin.rename(moved)
        plugin = moved
        if cli("moved_runtime_doctor", "doctor").get("status") != "local_checks_ready":
            raise CheckFailure("moved_runtime_doctor_not_ready")
        after = {
            path.relative_to(plugin).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in plugin.rglob("*")
            if path.is_file()
        }
        if after != {name: hashlib.sha256(data).hexdigest() for name, data in verified.items()}:
            raise CheckFailure("extracted_sources_changed")
    finally:
        if runtime.exists():
            removed = cli("runtime_remove", "remove")
            if removed.get("status") != "removed" or runtime.exists():
                raise CheckFailure("runtime_removal_incomplete")
    emit(
        check="exact_extraction_lifecycle",
        status="passed",
        sdk_version=SDK,
        prefill="not_requested",
        hook_activation="not_performed",
        host_enforcement="not_observed",
    )


def delivery_checks(
    source: Path,
    work: Path,
    archive: Path,
    checksum: str,
    verified: dict[str, bytes],
    runtime: Path,
    env: dict[str, str],
) -> None:
    """Exercise the shipped closure using the existing local SDK runtime."""
    delivery = delivery_module(source)
    if delivery.NATIVE_SHA256 != checksum:
        raise CheckFailure("delivery_native_identity_mismatch")
    first = delivery.build(source, work / "delivery-first", archive, checksum)
    second = delivery.build(source, work / "delivery-second", archive, checksum)
    if first["sha256"] != second["sha256"]:
        raise CheckFailure("delivery_build_not_reproducible")
    for built in (first, second):
        delivery.verify(Path(built["archive"]), built["sha256"])
    extracted = work / "standalone extracted helper with spaces"
    delivery.extract(Path(first["archive"]), first["sha256"], extracted)
    completed = run(
        "standalone_delivery_verify",
        [
            sys.executable,
            "-I",
            "-B",
            str(extracted / "scripts/cursor_delivery.py"),
            "verify",
            first["archive"],
            "--sha256",
            first["sha256"],
        ],
        cwd=work,
        env=env,
    )
    result = object_result(completed.stdout)
    if result.get("verified") is not True or result.get("native_sha256") != checksum:
        raise CheckFailure("standalone_delivery_unverified")
    workspace_work = work / "standalone delivery workspace checks"
    workspace_work.mkdir()
    workspace_checks(
        extracted,
        workspace_work,
        extracted / delivery.NATIVE_PATH,
        checksum,
        verified,
        runtime,
        env,
    )
    emit(
        check="standalone_helper_delivery",
        sha256=first["sha256"],
        native_sha256=checksum,
        reproducible=True,
        sdk_runtime="reused",
        activation="not_performed",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=(*PHASES, "all"), default="all")
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--uv", default="uv")
    args = parser.parse_args(argv)
    emit(
        target="cursor_native_offline",
        operating_system=platform.system(),
        architecture=platform.machine(),
        python=platform.python_version(),
        host_execution="not_performed",
    )
    if platform.system() != "Darwin" or sys.version_info[:2] != (3, 12):
        emit(status="failed", reason="macos_python312_required")
        return 1
    if not args.source.is_absolute() or not args.source.is_dir():
        emit(status="failed", reason="absolute_source_required")
        return 1
    source = args.source.resolve()
    functions = {
        "tests": test_checks,
        "static": static_checks,
        "artifacts": artifact_checks,
        "lifecycle": lifecycle_checks,
    }
    for phase in PHASES if args.phase == "all" else (args.phase,):
        try:
            with tempfile.TemporaryDirectory(
                prefix="guardtrellis-cursor-" + phase + "-"
            ) as temporary:
                functions[phase](source, Path(temporary).resolve(), args.uv)
        except Exception:
            # Child output and exception text can include fixture contents or operator paths.
            emit(phase=phase, status="failed", reason="native_offline_check_failed")
            return 1
        emit(phase=phase, status="passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
