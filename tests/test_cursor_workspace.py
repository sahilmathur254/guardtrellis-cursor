"""Project helper checks use unopened, owned synthetic workspaces only."""

from __future__ import annotations

import importlib.util
import io
import json
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cursor_workspace", ROOT / "scripts/cursor_workspace.py"
)
assert SPEC and SPEC.loader
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
boot = helper.boot


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gt-owned-workspace-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.workspace = self.root / "unopened workspace with spaces"
        self.workspace.mkdir()
        self.runtime = self.root / "external-runtime"
        built = helper.release.build(ROOT, self.root / "archive")
        self.archive, self.checksum = Path(built["archive"]), built["sha256"]
        self.python = Path(sys.executable).resolve()
        self.config = self.workspace / ".cursor/hooks.json"
        self.control = self.workspace / boot.CONTROL

    def install(self):
        return helper.install(
            self.workspace, self.archive, self.checksum, self.python, self.runtime
        )

    def write_config(self, value):
        self.config.parent.mkdir(exist_ok=True)
        self.config.write_text(json.dumps(value))

    def foreign(self):
        return {
            "version": 1,
            "hooks": {
                "afterFileEdit": [{"command": "/usr/bin/true", "private": "configuration-canary"}],
                "workspaceOpen": [{"command": "/usr/bin/true"}],
            },
            "custom": {"preserve": True},
        }

    def event(self):
        return json.dumps(
            {
                "hook_event_name": "workspaceOpen",
                "workspace_roots": [str(self.workspace)],
                "user_email": "ignored@example.org",
            }
        ).encode()

    def test_plan_is_inert_concrete_and_does_not_dump_foreign_values(self):
        self.write_config(self.foreign())
        before = self.config.read_bytes()
        plan = helper.plan(self.workspace, self.archive, self.checksum, self.python, self.runtime)
        self.assertEqual(plan["status"], "planned")
        self.assertEqual(len(plan["files"]), 25)
        self.assertEqual(plan["config_delta"]["existing_workspaceOpen_count"], 1)
        self.assertNotIn("configuration-canary", json.dumps(plan))
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.control.exists())
        self.assertFalse(self.runtime.exists())

    def test_install_health_and_remove_preserve_other_config_mode_and_runtime(self):
        original = self.foreign()
        self.write_config(original)
        self.config.chmod(0o640)
        self.runtime.mkdir()
        (self.runtime / "keep.txt").write_text("external runtime")
        self.assertEqual(self.install()["status"], "configuration_staged")
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o640)
        health = helper.health(self.workspace)
        self.assertEqual(health["runtime_check"]["status"], "not_requested")
        self.assertEqual(health["native_activation"], "not_observed")
        current = json.loads(self.config.read_bytes())
        current["hooks"]["afterFileEdit"].append({"command": "/usr/bin/false"})
        self.write_config(current)
        self.config.chmod(0o640)
        self.assertEqual(helper.health(self.workspace)["status"], "configuration_ready")
        self.assertTrue(helper.remove(self.workspace)["process_restart_required"])
        expected = original
        expected["hooks"]["afterFileEdit"].append({"command": "/usr/bin/false"})
        self.assertEqual(json.loads(self.config.read_bytes()), expected)
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o640)
        self.assertFalse(self.control.exists())
        self.assertEqual((self.runtime / "keep.txt").read_text(), "external runtime")

    def test_new_config_is_removed_and_later_unrelated_hooks_are_preserved(self):
        self.install()
        helper.remove(self.workspace)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.config.parent.exists())
        self.install()
        current = json.loads(self.config.read_bytes())
        current["hooks"]["afterFileEdit"] = [{"command": "/usr/bin/true"}]
        self.write_config(current)
        helper.remove(self.workspace)
        self.assertEqual(
            json.loads(self.config.read_bytes()),
            {"version": 1, "hooks": {"afterFileEdit": [{"command": "/usr/bin/true"}]}},
        )

    def test_repeat_and_enforcing_archive_are_refused(self):
        self.install()
        before = self.config.read_bytes()
        with self.assertRaises(boot.StateError):
            self.install()
        self.assertEqual(self.config.read_bytes(), before)
        helper.remove(self.workspace)
        built = helper.release.build(ROOT, self.root / "enforcing", "enforce-secrets-v1")
        with self.assertRaises(boot.StateError):
            helper.install(
                self.workspace, Path(built["archive"]), built["sha256"], self.python, self.runtime
            )
        self.assertFalse(self.control.exists())

    def test_invalid_json_duplicates_versions_depth_and_event_shapes_are_refused(self):
        self.config.parent.mkdir()
        for raw in (
            b'{"hooks":{},"hooks":{}}',
            b'{"version":true}',
            b'{"version":2}',
            b'{"hooks":{"workspaceOpen":{}}}',
            b'{"hooks":{"workspaceOpen":[{"command":2}]}}',
            b'{"unknown":NaN}',
            b"[" * 2000 + b"]" * 2000,
        ):
            self.config.write_bytes(raw)
            with self.subTest(raw=raw[:30]), self.assertRaises(boot.StateError):
                self.install()
            self.assertEqual(self.config.read_bytes(), raw)
            self.assertFalse(self.control.exists())

    def test_links_profiles_source_and_runtime_overlaps_are_refused(self):
        alias = self.root / "alias"
        alias.symlink_to(self.workspace, target_is_directory=True)
        for workspace, runtime in (
            (alias, self.runtime),
            (self.workspace, self.workspace / "runtime"),
            (ROOT, self.runtime),
            (Path.home() / ".cursor", self.runtime),
        ):
            with self.subTest(workspace=workspace), self.assertRaises((boot.StateError, OSError)):
                helper.plan(workspace, self.archive, self.checksum, self.python, runtime)
        outside = self.root / "outside"
        outside.mkdir()
        self.config.parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(boot.StateError):
            self.install()
        self.assertEqual(list(outside.iterdir()), [])

    def test_changed_owned_entry_duplicate_ledger_bootstrap_source_and_addition_refuse(self):
        self.install()
        for target, data in (
            (self.control / boot.STATE, b"{}"),
            (self.control / boot.BOOTSTRAP, b"changed"),
            (self.control / boot.PLUGIN / "README.md", b"changed"),
        ):
            original = target.read_bytes()
            target.write_bytes(data)
            with self.subTest(target=target), self.assertRaises((boot.StateError, OSError)):
                helper.remove(self.workspace)
            target.write_bytes(original)
        extra = self.control / "unowned.txt"
        extra.write_text("keep")
        with self.assertRaises(boot.StateError):
            helper.remove(self.workspace)
        self.assertEqual(extra.read_text(), "keep")
        extra.unlink()
        config = json.loads(self.config.read_bytes())
        original = self.config.read_bytes()
        config["hooks"]["workspaceOpen"].append(config["hooks"]["workspaceOpen"][0])
        self.write_config(config)
        with self.assertRaises(boot.StateError):
            helper.remove(self.workspace)
        self.config.write_bytes(original)
        helper.remove(self.workspace)

    def test_source_link_is_refused_without_touching_external_file(self):
        self.install()
        target = self.control / boot.PLUGIN / "README.md"
        original = target.read_bytes()
        target.unlink()
        external = self.root / "keep.txt"
        external.write_text("outside canary")
        target.symlink_to(external)
        with self.assertRaises(boot.StateError):
            helper.remove(self.workspace)
        self.assertEqual(external.read_text(), "outside canary")
        target.unlink()
        target.write_bytes(original)
        helper.remove(self.workspace)

    def test_bootstrap_accepts_only_exact_event_workspace_and_owned_integrity(self):
        self.install()
        state = self.control / boot.STATE
        checksum = boot.digest(state.read_bytes())
        expected = {"pluginPaths": [str(self.control / boot.PLUGIN)]}
        self.assertEqual(boot.handle(self.event(), state, checksum), expected)
        self.assertFalse(self.runtime.exists())
        for event in (
            b"{",
            b"x" * 65537,
            b'{"hook_event_name":"sessionStart"}',
            b'{"hook_event_name":"workspaceOpen","workspace_roots":["/wrong"]}',
        ):
            with self.subTest(event=event[:30]), self.assertRaises(boot.StateError):
                boot.handle(event, state, checksum)
        (self.workspace / "new-project-file.py").write_text("synthetic unrelated project change")
        self.assertEqual(boot.handle(self.event(), state, checksum), expected)
        with self.assertRaises(boot.StateError):
            boot.handle(self.event(), state, "0" * 64)

    def test_failed_staging_rolls_back_owned_state_and_preserves_config(self):
        self.write_config(self.foreign())
        before = self.config.read_bytes()
        original_write = helper._write_owned_tree

        def failed(*args):
            original_write(*args)
            raise OSError("synthetic failure")

        with patch.object(helper, "_write_owned_tree", side_effect=failed):
            with self.assertRaises(boot.StateError):
                self.install()
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.control.exists())

    def test_concurrent_config_change_is_preserved_with_recoverable_owned_state(self):
        self.write_config(self.foreign())
        original_atomic = helper._atomic_config

        def changed(workspace, data, before, mode):
            self.write_config({"version": 1, "hooks": {}, "user_added": "preserve"})
            return original_atomic(workspace, data, before, mode)

        with patch.object(helper, "_atomic_config", side_effect=changed):
            with self.assertRaises(boot.StateError):
                self.install()
        self.assertEqual(json.loads(self.config.read_bytes())["user_added"], "preserve")
        self.assertTrue((self.control / boot.STATE).exists())

    def test_runtime_execution_is_explicit_and_health_never_asserts_gui_activation(self):
        self.install()
        with patch.object(helper.subprocess, "run") as run:
            self.assertEqual(
                helper.health(self.workspace)["runtime_check"]["status"], "not_requested"
            )
            run.assert_not_called()
        with patch.object(helper.subprocess, "run", side_effect=OSError("synthetic")):
            report = helper.health(self.workspace, True)
        self.assertEqual(report["runtime_check"]["status"], "unavailable")
        self.assertEqual(report["runtime_handoff"]["gui_environment"], "not_observed")

    def test_cli_failures_are_static_and_do_not_echo_config_values(self):
        self.write_config({"version": 2, "secret": "private-canary"})
        output = io.StringIO()
        with redirect_stderr(output):
            result = helper.main(
                [
                    "install",
                    "--workspace",
                    str(self.workspace),
                    "--archive",
                    str(self.archive),
                    "--sha256",
                    self.checksum,
                    "--runtime",
                    str(self.runtime),
                ]
            )
        self.assertEqual(result, 1)
        self.assertNotIn("private-canary", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["reason"], "unsupported_config_version")

    def test_python_symlink_loop_returns_static_refusal_before_writes(self):
        first, second = self.root / "python-a", self.root / "python-b"
        first.symlink_to(second)
        second.symlink_to(first)
        output = io.StringIO()
        with redirect_stderr(output):
            result = helper.main(
                [
                    "install",
                    "--workspace",
                    str(self.workspace),
                    "--archive",
                    str(self.archive),
                    "--sha256",
                    self.checksum,
                    "--runtime",
                    str(self.runtime),
                    "--python",
                    str(first),
                ]
            )
        self.assertEqual(result, 1)
        self.assertEqual(json.loads(output.getvalue())["reason"], "bootstrap_python_unavailable")
        self.assertFalse(self.control.exists())
        self.assertFalse(self.config.exists())

    def test_initial_control_swap_cannot_overwrite_outside_ledger(self):
        outside = self.root / "outside-control"
        outside.mkdir()
        sentinel = outside / boot.STATE
        sentinel.write_text("outside ledger sentinel")
        original = helper.os.mkdir
        swapped = False

        def swap(name, *args, **kwargs):
            nonlocal swapped
            result = original(name, *args, **kwargs)
            if name == boot.CONTROL and kwargs.get("dir_fd") is not None and not swapped:
                swapped = True
                self.control.rename(self.workspace / "retired-control")
                self.control.symlink_to(outside, target_is_directory=True)
            return result

        with patch.object(helper.os, "mkdir", side_effect=swap):
            with self.assertRaises(boot.StateError):
                self.install()
        self.assertTrue(swapped)
        self.assertEqual(sentinel.read_text(), "outside ledger sentinel")
        self.assertEqual({path.name for path in outside.iterdir()}, {boot.STATE})

    def test_requested_runtime_unavailable_is_nonzero_with_separate_configuration_status(self):
        self.install()
        output = io.StringIO()
        with (
            patch.object(helper.subprocess, "run", side_effect=OSError("synthetic")),
            redirect_stdout(output),
        ):
            result = helper.main(["health", "--workspace", str(self.workspace), "--check-runtime"])
        self.assertEqual(result, 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "configuration_ready")
        self.assertEqual(report["runtime_check"]["status"], "unavailable")

    def test_config_parent_swap_cannot_write_outside_sentinel(self):
        self.write_config(self.foreign())
        outside = self.root / "outside-config"
        outside.mkdir()
        sentinel = outside / "hooks.json"
        sentinel.write_text("outside configuration sentinel")
        original = helper._parent_fd
        swapped = False

        def swap(file):
            nonlocal swapped
            descriptor = original(file)
            if file == self.config and not swapped:
                swapped = True
                self.config.parent.rename(self.workspace / "retired-cursor")
                self.config.parent.symlink_to(outside, target_is_directory=True)
            return descriptor

        with patch.object(helper, "_parent_fd", side_effect=swap):
            with self.assertRaises(boot.StateError):
                self.install()
        self.assertTrue(swapped)
        self.assertEqual(sentinel.read_text(), "outside configuration sentinel")
        self.assertEqual({path.name for path in outside.iterdir()}, {"hooks.json"})

    def test_removal_parent_swap_cannot_unlink_outside_matching_source(self):
        self.install()
        common = self.control / boot.PLUGIN / "adapters/common"
        outside = self.root / "outside-sources"
        outside.mkdir()
        saved = {path.name: path.read_bytes() for path in common.iterdir()}
        for name, data in saved.items():
            (outside / name).write_bytes(data)
        original = helper._parent_fd
        swapped = False

        def swap(file):
            nonlocal swapped
            descriptor = original(file)
            if file.parent == common and not swapped:
                swapped = True
                common.rename(common.with_name("retired-common"))
                common.symlink_to(outside, target_is_directory=True)
            return descriptor

        with patch.object(helper, "_parent_fd", side_effect=swap):
            with self.assertRaises((boot.StateError, OSError)):
                helper.remove(self.workspace)
        self.assertTrue(swapped)
        self.assertEqual({path.name: path.read_bytes() for path in outside.iterdir()}, saved)

    def test_standalone_bootstrap_stdio_is_bounded_and_content_free(self):
        self.install()
        state = self.control / boot.STATE
        command = [
            str(self.python),
            "-I",
            "-B",
            str(self.control / boot.BOOTSTRAP),
            "--state",
            str(state),
            "--sha256",
            boot.digest(state.read_bytes()),
        ]
        for valid, raw in ((True, self.event()), (False, b"{"), (False, b"x" * 65537)):
            result = subprocess.run(command, input=raw, capture_output=True, timeout=5, check=True)
            paths = [str(self.control / boot.PLUGIN)] if valid else []
            self.assertEqual(json.loads(result.stdout), {"pluginPaths": paths})
            self.assertNotIn(b"ignored@example.org", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
