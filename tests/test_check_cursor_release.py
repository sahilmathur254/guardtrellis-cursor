"""Runner orchestration tests use temporary roots, inert children and mocked setup."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cursor_offline_checks", ROOT / "scripts/check_cursor_release.py"
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class NativeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gt-cursor-runner-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "source with spaces"
        self.source.mkdir()
        self.work = self.root / "owned scratch"
        self.work.mkdir()
        self.stdout = io.StringIO()

    def test_child_failure_propagates_without_printing_captured_content(self):
        child = subprocess.CompletedProcess(
            [], 7, b"synthetic-private-output", b"synthetic-private-error"
        )
        with (
            patch.object(runner.subprocess, "run", return_value=child) as execute,
            redirect_stdout(self.stdout),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.run("synthetic_stage", ["/inert"], cwd=self.work, env={})
        self.assertEqual(
            json.loads(self.stdout.getvalue()),
            {
                "check": "synthetic_stage",
                "process": "failed",
                "exit_code": 7,
            },
        )
        self.assertTrue(execute.call_args.kwargs["capture_output"])
        self.assertFalse(execute.call_args.kwargs["check"])

    def test_child_launch_and_timeout_failures_are_static(self):
        for failure in (OSError("private-path"), subprocess.TimeoutExpired("private-arg", 1)):
            with self.subTest(failure=type(failure).__name__):
                output = io.StringIO()
                with (
                    patch.object(runner.subprocess, "run", side_effect=failure),
                    redirect_stdout(output),
                    self.assertRaises(runner.CheckFailure),
                ):
                    runner.run("synthetic_stage", ["/inert"], cwd=self.work, env={})
                self.assertNotIn("private", output.getvalue())

    def test_actual_inert_child_is_captured_from_unrelated_directory(self):
        with redirect_stdout(self.stdout):
            result = runner.run(
                "inert_child",
                [sys.executable, "-I", "-B", "-c", "print('synthetic output')"],
                cwd=self.work,
                env=runner.environment(self.work),
            )
        self.assertEqual(result.stdout, b"synthetic output\n")
        self.assertNotIn("synthetic output", self.stdout.getvalue())

    def test_test_counts_are_recorded_and_empty_discovery_fails(self):
        for diagnostic in (b"Ran 0 tests in 0s\n", b"unexpected output"):
            with (
                patch.object(
                    runner.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0, b"", diagnostic),
                ),
                self.assertRaises(runner.CheckFailure),
            ):
                runner.run("tests", ["/inert"], cwd=self.work, env={}, tests=True)
        with (
            patch.object(
                runner.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, b"", b"Ran 32 tests in 1s\nOK\n"),
            ),
            redirect_stdout(self.stdout),
        ):
            runner.run("tests", ["/inert"], cwd=self.work, env={}, tests=True)
        self.assertEqual(json.loads(self.stdout.getvalue())["tests"], 32)

    def test_cache_is_copied_and_uv_cannot_write_the_seed(self):
        seed = self.root / "original cache"
        seed.mkdir()
        (seed / "locked-package").write_text("original")
        home = os.environ.get("HOME")
        with patch.dict(
            os.environ,
            {
                "UV_CACHE_DIR": str(seed),
                "UV_PROJECT_ENVIRONMENT": "/unrelated",
                "UV_PROJECT": "/unrelated",
                "PYTHONPATH": "/unrelated",
            },
        ):
            env = runner.environment(self.work, cache=True)
        copied = Path(env["UV_CACHE_DIR"])
        self.assertTrue(copied.is_relative_to(self.work))
        (copied / "locked-package").write_text("changed scratch")
        self.assertEqual((seed / "locked-package").read_text(), "original")
        self.assertNotIn("UV_PROJECT_ENVIRONMENT", env)
        self.assertNotIn("UV_PROJECT", env)
        self.assertNotIn("PYTHONPATH", env)
        self.assertEqual(env["UV_PYTHON_DOWNLOADS"], "never")
        self.assertEqual(os.environ.get("HOME"), home)

    def test_zero_exit_with_skipped_native_tests_fails_and_records_count(self):
        child = subprocess.CompletedProcess([], 0, b"", b"Ran 32 tests in 1s\nOK (skipped=32)\n")
        with (
            patch.object(runner.subprocess, "run", return_value=child),
            redirect_stdout(self.stdout),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.run("native_launcher_tests", ["/inert"], cwd=self.work, env={}, tests=True)
        self.assertEqual(
            json.loads(self.stdout.getvalue()),
            {
                "check": "native_launcher_tests",
                "process": "failed",
                "tests": 32,
                "skipped": 32,
            },
        )

    def test_relative_cache_seed_is_rejected_without_mutation(self):
        with (
            patch.dict(os.environ, {"UV_CACHE_DIR": "relative"}),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.environment(self.work, cache=True)
        self.assertEqual(list(self.work.iterdir()), [])

    def test_uv_is_existing_and_exact_version(self):
        with (
            patch.object(runner.shutil, "which", return_value=None),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.uv_executable("not-installed", self.work, {})
        with (
            patch.object(runner.shutil, "which", return_value="/inert/uv"),
            patch.object(
                runner, "run", return_value=subprocess.CompletedProcess([], 0, b"uv 9.0.0\n", b"")
            ),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.uv_executable("uv", self.work, {})

    def test_selected_test_files_run_once_without_full_legacy_suite(self):
        for name in runner.TEST_FILES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# inert discovery target\n")
        with patch.object(runner, "run") as execute:
            runner.test_checks(self.source, self.work, "uv")
        self.assertEqual(execute.call_count, len(runner.TEST_FILES))
        patterns = [call.args[1][-2] for call in execute.call_args_list]
        self.assertEqual(patterns, [Path(name).name for name in runner.TEST_FILES])
        for call in execute.call_args_list:
            self.assertEqual(call.kwargs["cwd"], self.work)
            self.assertTrue(call.kwargs["tests"])

    def test_artifacts_propagate_canonical_drift_before_any_build(self):
        builder = SimpleNamespace(
            check_export=Mock(side_effect=runner.CheckFailure()), build=Mock()
        )
        with (
            patch.object(runner, "builder_module", return_value=builder),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.artifact_checks(self.source, self.work, "uv")
        builder.check_export.assert_called_once_with(self.source, check_catalog=True)
        builder.build.assert_not_called()

    def test_artifacts_detect_nondeterminism(self):
        builder = SimpleNamespace(
            check_export=Mock(return_value={"verified": True, "profile": "advisory"}),
            build=Mock(side_effect=[{"sha256": "first"}, {"sha256": "second"}]),
            verify=Mock(),
        )
        with (
            patch.object(runner, "builder_module", return_value=builder),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.artifact_checks(self.source, self.work, "uv")
        builder.verify.assert_not_called()

    def test_artifact_profiles_are_fixed_and_each_build_verified(self):
        def build(source, destination, profile):
            self.assertEqual(source, self.source)
            self.assertTrue(destination.is_relative_to(self.work))
            return {"sha256": profile, "archive": str(destination / profile)}

        def verify(archive, checksum):
            self.assertEqual(archive.name, checksum)
            return {"MANIFEST": json.dumps({"profile": checksum}).encode()}

        builder = SimpleNamespace(
            MANIFEST="MANIFEST",
            check_export=Mock(return_value={"verified": True, "profile": "advisory"}),
            build=Mock(side_effect=build),
            verify=Mock(side_effect=verify),
        )
        with (
            patch.object(runner, "builder_module", return_value=builder),
            redirect_stdout(self.stdout),
        ):
            runner.artifact_checks(self.source, self.work, "uv")
        self.assertEqual(
            [call.args[2] for call in builder.build.call_args_list],
            ["advisory", "advisory", "enforce-secrets-v1", "enforce-secrets-v1"],
        )
        self.assertEqual(builder.verify.call_count, 4)

    def test_lifecycle_failure_attempts_owned_removal_without_open(self):
        files = {"owned.txt": b"inert source"}

        def extract(archive, checksum, destination):
            destination.mkdir()
            (destination / "owned.txt").write_bytes(files["owned.txt"])

        builder = SimpleNamespace(
            build=Mock(return_value={"archive": str(self.work / "inert.zip"), "sha256": "inert"}),
            verify=Mock(return_value=files),
            extract=Mock(side_effect=extract),
        )
        calls = []

        def execute(label, command, **kwargs):
            calls.append((label, command))
            runtime = Path(kwargs["env"]["GUARDTRELLIS_CURSOR_RUNTIME"])
            self.assertTrue(runtime.is_relative_to(self.work))
            self.assertNotIn("--open", command)
            if label == "runtime_setup":
                runtime.mkdir()
                data = {"status": "ready", "sdk_version": "0.1.9"}
            elif label == "runtime_doctor":
                raise runner.CheckFailure("synthetic_failure")
            else:
                self.assertEqual(label, "runtime_remove")
                runtime.rmdir()
                data = {"status": "removed"}
            return subprocess.CompletedProcess(command, 0, json.dumps(data).encode(), b"")

        with (
            patch.object(runner, "builder_module", return_value=builder),
            patch.object(runner, "environment", return_value={}),
            patch.object(runner, "uv_executable", return_value="/inert/uv"),
            patch.object(runner, "run", side_effect=execute),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.lifecycle_checks(self.source, self.work, "uv")
        self.assertEqual(
            [label for label, _ in calls], ["runtime_setup", "runtime_doctor", "runtime_remove"]
        )
        self.assertFalse((self.work / "owned external runtime with spaces").exists())

    def workspace_fixture(
        self, *, runtime_status="local_checks_ready", changed_source=False, changed_plan=False
    ):
        runtime = self.work / "existing owned runtime"
        runtime.mkdir()
        ledger = runtime / ".guardtrellis-cursor-runtime.json"
        ledger.write_bytes(b"owned runtime record")
        calls = []

        def execute(label, command, **kwargs):
            calls.append((label, command))
            self.assertEqual(kwargs["cwd"], self.work)
            self.assertEqual(command[:3], [sys.executable, "-I", "-B"])
            self.assertEqual(command[3], str(self.source / "scripts/cursor_workspace.py"))
            self.assertNotIn("--open", command)
            self.assertNotIn("--dest", command)
            operation = command[4]
            workspace = Path(command[command.index("--workspace") + 1])
            self.assertTrue(workspace.is_relative_to(self.work))
            control = workspace / ".guardtrellis-cursor"
            configuration = workspace / ".cursor/hooks.json"
            if operation == "plan":
                if changed_plan:
                    configuration.write_text("{}")
                data = {"status": "planned", "activation": "not_performed"}
            elif operation == "install":
                self.assertEqual(command[command.index("--runtime") + 1], str(runtime))
                plugin = control / "guardtrellis-cursor"
                plugin.mkdir(parents=True)
                (plugin / "owned.txt").write_bytes(
                    b"different" if changed_source else b"inert source"
                )
                config = json.loads(configuration.read_bytes())
                config["hooks"]["workspaceOpen"] = [{"command": "inert owned bootstrap"}]
                configuration.write_text(json.dumps(config))
                data = {
                    "status": "configuration_staged",
                    "activation": "not_performed",
                    "runtime_action": "not_modified",
                }
            elif operation == "health":
                self.assertIn("--check-runtime", command)
                data = {
                    "status": "configuration_ready",
                    "native_activation": "not_observed",
                    "runtime_check": {"status": runtime_status},
                }
            else:
                self.assertEqual(operation, "remove")
                plugin = control / "guardtrellis-cursor"
                (plugin / "owned.txt").unlink()
                plugin.rmdir()
                control.rmdir()
                config = json.loads(configuration.read_bytes())
                del config["hooks"]["workspaceOpen"]
                configuration.write_text(json.dumps(config))
                data = {
                    "status": "configuration_removed",
                    "native_unload": "not_observed",
                    "process_restart_required": True,
                    "runtime_action": "not_modified",
                }
            return subprocess.CompletedProcess(command, 0, json.dumps(data).encode(), b"")

        return runtime, ledger, calls, execute

    def test_workspace_helper_reuses_runtime_and_preserves_foreign_hook(self):
        runtime, ledger, calls, execute = self.workspace_fixture()
        with patch.object(runner, "run", side_effect=execute), redirect_stdout(self.stdout):
            runner.workspace_checks(
                self.source,
                self.work,
                self.root / "archive.zip",
                "inert-checksum",
                {"owned.txt": b"inert source"},
                runtime,
                {},
            )
        self.assertEqual(
            [label for label, _ in calls],
            ["workspace_plan", "workspace_install", "workspace_health", "workspace_remove"],
        )
        workspace = self.work / "unopened owned workspace with spaces"
        self.assertFalse((workspace / ".guardtrellis-cursor").exists())
        self.assertEqual(
            json.loads((workspace / ".cursor/hooks.json").read_bytes()),
            {
                "version": 1,
                "hooks": {"afterFileEdit": [{"command": "/usr/bin/true"}]},
            },
        )
        self.assertEqual(ledger.read_bytes(), b"owned runtime record")
        self.assertEqual(json.loads(self.stdout.getvalue())["activation"], "not_performed")

    def test_workspace_unavailable_runtime_propagates_after_owned_removal(self):
        runtime, ledger, calls, execute = self.workspace_fixture(runtime_status="unavailable")
        with (
            patch.object(runner, "run", side_effect=execute),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.workspace_checks(
                self.source,
                self.work,
                self.root / "archive.zip",
                "inert-checksum",
                {"owned.txt": b"inert source"},
                runtime,
                {},
            )
        self.assertEqual(calls[-1][0], "workspace_remove")
        self.assertFalse(
            (self.work / "unopened owned workspace with spaces/.guardtrellis-cursor").exists()
        )
        self.assertEqual(ledger.read_bytes(), b"owned runtime record")

    def test_workspace_wrong_extraction_fails_before_health_and_removes_owned_files(self):
        runtime, ledger, calls, execute = self.workspace_fixture(changed_source=True)
        with (
            patch.object(runner, "run", side_effect=execute),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.workspace_checks(
                self.source,
                self.work,
                self.root / "archive.zip",
                "inert-checksum",
                {"owned.txt": b"inert source"},
                runtime,
                {},
            )
        self.assertEqual(
            [label for label, _ in calls],
            ["workspace_plan", "workspace_install", "workspace_remove"],
        )
        self.assertEqual(ledger.read_bytes(), b"owned runtime record")

    def test_workspace_dry_run_mutation_is_rejected_before_install(self):
        runtime, ledger, calls, execute = self.workspace_fixture(changed_plan=True)
        with (
            patch.object(runner, "run", side_effect=execute),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.workspace_checks(
                self.source,
                self.work,
                self.root / "archive.zip",
                "inert-checksum",
                {"owned.txt": b"inert source"},
                runtime,
                {},
            )
        self.assertEqual([label for label, _ in calls], ["workspace_plan"])
        self.assertEqual(ledger.read_bytes(), b"owned runtime record")

    def test_static_tools_use_copied_lock_and_scratch_environment(self):
        project = self.source / "plugins/guardtrellis/adapters/codex"
        project.mkdir(parents=True)
        for name in ("pyproject.toml", "uv.lock"):
            (project / name).write_text("inert locked input: " + name)
        with (
            patch.object(runner, "environment", return_value={}),
            patch.object(runner, "uv_executable", return_value="/inert/uv"),
            patch.object(runner, "run") as execute,
        ):
            runner.static_checks(self.source, self.work, "uv")
        self.assertEqual(execute.call_count, 5)
        for name in ("pyproject.toml", "uv.lock"):
            self.assertEqual(
                (self.work / "tool-project" / name).read_bytes(), (project / name).read_bytes()
            )
        for call in execute.call_args_list:
            self.assertEqual(call.kwargs["cwd"], self.work)
            self.assertTrue(
                Path(call.kwargs["env"]["UV_PROJECT_ENVIRONMENT"]).is_relative_to(self.work)
            )
        self.assertIn("--locked", execute.call_args_list[0].args[1])
        self.assertIn("--strict", execute.call_args_list[3].args[1])
        for target in ("scripts/cursor_workspace.py", "integrations/cursor/bootstrap.py"):
            self.assertIn(str(self.source / target), execute.call_args_list[1].args[1])
            self.assertIn(str(self.source / target), execute.call_args_list[3].args[1])
        public_copy = str(self.source / "tests/test_cursor_public_copy.py")
        self.assertIn(public_copy, execute.call_args_list[1].args[1])
        self.assertIn(public_copy, execute.call_args_list[2].args[1])

    def test_main_failure_stops_later_phases_and_cleans_owned_scratch(self):
        workspaces = []

        def fail(source, work, uv):
            workspaces.append(work)
            (work / "owned.txt").write_text("owned synthetic data")
            raise runner.CheckFailure("do-not-print-private-exception")

        with (
            patch.object(runner.platform, "system", return_value="Darwin"),
            patch.object(runner.sys, "version_info", (3, 12, 0)),
            patch.object(runner, "test_checks", side_effect=fail),
            patch.object(runner, "static_checks") as later,
            redirect_stdout(self.stdout),
        ):
            status = runner.main(["--source", str(self.source), "--phase", "all"])
        self.assertEqual(status, 1)
        later.assert_not_called()
        self.assertTrue(workspaces)
        self.assertTrue(all(not path.exists() for path in workspaces))
        self.assertNotIn("do-not-print", self.stdout.getvalue())
        self.assertTrue(self.source.is_dir())

    def test_source_override_decouples_runner_from_its_checkout(self):
        observed = []
        with (
            patch.object(runner.platform, "system", return_value="Darwin"),
            patch.object(runner.sys, "version_info", (3, 12, 0)),
            patch.object(
                runner,
                "artifact_checks",
                side_effect=lambda source, work, uv: observed.append((source, work, uv)),
            ),
            redirect_stdout(self.stdout),
        ):
            self.assertEqual(
                runner.main(
                    ["--source", str(self.source), "--phase", "artifacts", "--uv", "/inert/uv"]
                ),
                0,
            )
        self.assertEqual(observed[0][0], self.source)
        self.assertEqual(observed[0][2], "/inert/uv")
        self.assertFalse(observed[0][1].exists())

    def test_relative_source_or_wrong_platform_does_not_run_checks(self):
        for system, source in (("Darwin", "relative"), ("Linux", str(self.source))):
            with (
                patch.object(runner.platform, "system", return_value=system),
                patch.object(runner.sys, "version_info", (3, 12, 0)),
                patch.object(runner, "test_checks") as execute,
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(runner.main(["--source", source, "--phase", "tests"]), 1)
            execute.assert_not_called()

    def test_nonobject_child_metadata_is_an_explicit_failure(self):
        for value in (b"[]", b"null", b"invalid", b"[" * 2000):
            with self.subTest(value=value[:8]), self.assertRaises(runner.CheckFailure):
                runner.object_result(value)

    def delivery_fixture(self, *, nondeterministic=False, wrong_verification=False):
        checksum = "native-checksum"
        builds = [
            {"archive": str(self.work / "first.zip"), "sha256": "bundle"},
            {
                "archive": str(self.work / "second.zip"),
                "sha256": "other" if nondeterministic else "bundle",
            },
        ]

        def extract(archive, digest, destination):
            destination.mkdir()

        delivery = SimpleNamespace(
            NATIVE_SHA256=checksum,
            NATIVE_PATH="artifacts/native.zip",
            build=Mock(side_effect=builds),
            verify=Mock(return_value={"owned": b"fixture"}),
            extract=Mock(side_effect=extract),
        )
        child = subprocess.CompletedProcess(
            [],
            0,
            json.dumps({"verified": not wrong_verification, "native_sha256": checksum}).encode(),
            b"",
        )
        return checksum, delivery, child

    def test_standalone_delivery_uses_extracted_helper_and_existing_runtime(self):
        checksum, delivery, child = self.delivery_fixture()
        runtime = self.work / "existing SDK runtime"
        with (
            patch.object(runner, "delivery_module", return_value=delivery),
            patch.object(runner, "run", return_value=child) as execute,
            patch.object(runner, "workspace_checks") as workspace,
            redirect_stdout(self.stdout),
        ):
            runner.delivery_checks(
                self.source,
                self.work,
                self.root / "native.zip",
                checksum,
                {"owned.txt": b"inert"},
                runtime,
                {},
            )
        extracted = self.work / "standalone extracted helper with spaces"
        self.assertEqual(workspace.call_args.args[0], extracted)
        self.assertEqual(workspace.call_args.args[2], extracted / "artifacts/native.zip")
        self.assertEqual(workspace.call_args.args[5], runtime)
        self.assertEqual(delivery.build.call_count, 2)
        self.assertEqual(delivery.verify.call_count, 2)
        self.assertEqual(
            execute.call_args.args[1][3], str(extracted / "scripts/cursor_delivery.py")
        )
        self.assertNotIn("setup", execute.call_args.args[1])

    def test_delivery_nondeterminism_or_failed_verification_stops_before_workspace(self):
        for nondeterministic, wrong in ((True, False), (False, True)):
            checksum, delivery, child = self.delivery_fixture(
                nondeterministic=nondeterministic, wrong_verification=wrong
            )
            with (
                patch.object(runner, "delivery_module", return_value=delivery),
                patch.object(runner, "run", return_value=child),
                patch.object(runner, "workspace_checks") as workspace,
                self.assertRaises(runner.CheckFailure),
            ):
                runner.delivery_checks(
                    self.source,
                    self.work,
                    self.root / "native.zip",
                    checksum,
                    {},
                    self.work / "runtime",
                    {},
                )
            workspace.assert_not_called()
            if (self.work / "standalone extracted helper with spaces").exists():
                (self.work / "standalone extracted helper with spaces").rmdir()

    def test_delivery_native_identity_mismatch_fails_before_build(self):
        checksum, delivery, child = self.delivery_fixture()
        with (
            patch.object(runner, "delivery_module", return_value=delivery),
            self.assertRaises(runner.CheckFailure),
        ):
            runner.delivery_checks(
                self.source,
                self.work,
                self.root / "native.zip",
                "wrong",
                {},
                self.work / "runtime",
                {},
            )
        delivery.build.assert_not_called()
        self.assertIn("scripts/cursor_delivery.py", runner.TOOL_FILES)
        self.assertIn("plugins/guardtrellis/adapters/cursor/prepare_prompt.py", runner.TOOL_FILES)
        self.assertIn("integrations/cursor/tests/test_prefill.py", runner.TEST_FILES)
        self.assertIn("tests/test_cursor_delivery.py", runner.TEST_FILES)


if __name__ == "__main__":
    unittest.main()
