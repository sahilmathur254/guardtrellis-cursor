"""Runtime lifecycle checks use owned temporary roots and mocked setup only."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "integrations/cursor/plugin/scripts/runtime_setup.py"
SPEC = importlib.util.spec_from_file_location("cursor_runtime_setup", PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gt-cursor-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.plugin = self.root / "plugin with spaces"
        sources = {
            "runtime/pyproject.toml": "plugins/guardtrellis/adapters/codex/pyproject.toml",
            "runtime/uv.lock": "plugins/guardtrellis/adapters/codex/uv.lock",
        }
        for name in runtime.SOURCES:
            original = ROOT / sources.get(name, "plugins/guardtrellis/" + name)
            target = self.plugin / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
        self.destination = self.root / "external runtime with spaces"

    def create(self, *, failed=False, health_failed=False):
        version = subprocess.CompletedProcess([], 0, b"3.12\n", b"")

        def install(command, **kwargs):
            self.command, self.env = command, kwargs["env"]
            binary = self.destination / "bin"
            binary.mkdir(exist_ok=True)
            if not (binary / "python").exists():
                (binary / "python").symlink_to(Path(sys.executable).resolve())
            (self.destination / "owned.txt").write_text("synthetic runtime payload")
            return subprocess.CompletedProcess(command, int(failed), b"", b"")

        with (
            patch.object(runtime.shutil, "which", return_value="/synthetic/uv"),
            patch.object(runtime, "run_local", return_value=version),
            patch.object(runtime.subprocess, "run", side_effect=install),
            patch.object(
                runtime,
                "health",
                side_effect=runtime.RuntimeErrorSafe("synthetic failure")
                if health_failed
                else None,
            ),
        ):
            return runtime.setup(self.destination, self.plugin, Path(sys.executable))

    def test_missing_uv_fails_without_creating_destination(self):
        with patch.object(runtime.shutil, "which", return_value=None):
            with self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.setup(self.destination, self.plugin, Path(sys.executable))
        self.assertFalse(self.destination.exists())

    def test_setup_uses_existing_python_locked_external_environment(self):
        with patch.dict(
            os.environ,
            {
                "UV_PROJECT": "/unrelated",
                "UV_PROJECT_ENVIRONMENT": "/unrelated-env",
                "PYTHONPATH": "/untrusted",
            },
        ):
            result = self.create()
        self.assertEqual(result["status"], "ready")
        self.assertEqual(self.env["UV_PROJECT_ENVIRONMENT"], str(self.destination))
        self.assertEqual(self.env["UV_PYTHON_DOWNLOADS"], "never")
        self.assertNotIn("UV_PROJECT", self.env)
        self.assertNotIn("PYTHONPATH", self.env)
        self.assertIn("--locked", self.command)
        self.assertIn("--no-dev", self.command)
        self.assertEqual((self.destination / runtime.MARKER).read_text(), runtime.TAG + "\n")
        self.assertEqual(runtime.load_record(self.destination)["status"], "ready")
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.setup(self.destination, self.plugin, Path(sys.executable))

    def test_failed_setup_and_failed_health_preserve_removable_partial_record(self):
        for failed, health_failed in ((True, False), (False, True)):
            with self.subTest(failed=failed, health_failed=health_failed):
                with self.assertRaises(runtime.RuntimeErrorSafe):
                    self.create(failed=failed, health_failed=health_failed)
                self.assertFalse((self.destination / runtime.MARKER).exists())
                self.assertEqual(runtime.load_record(self.destination)["status"], "incomplete")
                runtime.remove(self.destination, self.plugin)
                self.assertFalse(self.destination.exists())

    def test_doctor_and_removal_work_after_plugin_move(self):
        self.create()
        moved = self.root / "moved plugin with spaces"
        self.plugin.rename(moved)
        with patch.object(runtime, "health") as health:
            result = runtime.doctor(self.destination, moved)
            health.assert_called_once_with(self.destination, moved)
        self.assertEqual(result["host_enforcement"], "not_observed")
        self.assertEqual(runtime.remove(self.destination, moved)["status"], "removed")
        self.assertTrue(moved.is_dir())

    def test_modified_and_added_runtime_entries_block_all_removal(self):
        for added in (False, True):
            with self.subTest(added=added):
                self.create()
                target = self.destination / ("new.txt" if added else "owned.txt")
                original = target.read_bytes() if target.exists() else None
                target.write_text("user-owned change")
                before = runtime.inventory(self.destination)
                with self.assertRaises(runtime.RuntimeErrorSafe):
                    runtime.remove(self.destination, self.plugin)
                self.assertEqual(runtime.inventory(self.destination), before)
                if original is None:
                    target.unlink()
                else:
                    target.write_bytes(original)
                runtime.remove(self.destination, self.plugin)

    def test_symlink_substitution_preserves_external_directory(self):
        self.create()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep")
        (self.destination / "bin/python").unlink()
        (self.destination / "bin").rmdir()
        (self.destination / "bin").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.remove(self.destination, self.plugin)
        self.assertEqual((outside / "keep.txt").read_text(), "keep")

    def test_profiles_plugin_relative_and_root_symlink_destinations_are_rejected(self):
        for destination in (
            Path("relative"),
            self.plugin / "venv",
            self.plugin.parent,
            Path.home() / ".cursor/new-runtime",
            Path.home() / "Library/Application Support/Cursor/new-runtime",
        ):
            with self.subTest(destination=destination), self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.destination(destination, self.plugin)
        self.destination.symlink_to(self.root / "absent")
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.destination(self.destination, self.plugin)

    def test_environment_override_is_absolute_and_does_not_repurpose_home(self):
        home = os.environ.get("HOME")
        with patch.dict(os.environ, {"GUARDTRELLIS_CURSOR_RUNTIME": str(self.destination)}):
            self.assertEqual(runtime.default_destination(), self.destination)
        self.assertEqual(os.environ.get("HOME"), home)

    def test_symlink_alias_to_normal_profile_is_rejected(self):
        alias = self.root / "profile-alias"
        alias.symlink_to(Path.home() / ".cursor", target_is_directory=True)
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.destination(alias / "new-runtime", self.plugin)

    def test_corrupt_or_forged_record_and_source_change_are_rejected(self):
        self.create()
        record_path = self.destination / runtime.RECORD
        original = record_path.read_bytes()
        record = json.loads(original)
        record["root"] = str(self.root)
        record_path.write_text(json.dumps(record))
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.remove(self.destination, self.plugin)
        record_path.write_bytes(original)
        (self.plugin / "adapters/common/prompt_runtime.py").write_text("changed source")
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.doctor(self.destination, self.plugin)
        runtime.remove(self.destination, self.plugin)

    def test_unrecorded_runtime_is_never_removed(self):
        self.destination.mkdir()
        (self.destination / "keep.txt").write_text("keep")
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.remove(self.destination, self.plugin)
        self.assertTrue((self.destination / "keep.txt").is_file())

    def test_malformed_lock_core_types_fail_safely(self):
        for value in ("package = [1, 2]\n", 'package = "invalid"\n'):
            (self.plugin / "runtime/uv.lock").write_text(value)
            with self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.source_map(self.plugin)

    def test_non_object_health_diagnostics_fail_safely(self):
        binary = self.destination / "bin"
        binary.mkdir(parents=True)
        (binary / "python").symlink_to(Path(sys.executable).resolve())
        responses = [
            subprocess.CompletedProcess([], 0, b"0.1.9\n", b""),
            subprocess.CompletedProcess([], 0, b'{"continue":true}', b""),
            subprocess.CompletedProcess(
                [],
                0,
                json.dumps(
                    {
                        "continue": False,
                        "user_message": (
                            "GuardTrellis detected a recognized secret pattern. "
                            "Remove it and resubmit."
                        ),
                    }
                ).encode(),
                b"[]",
            ),
        ]
        with patch.object(runtime, "run_local", side_effect=responses):
            with self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.health(self.destination, self.plugin)

    def test_doctor_rechecks_runtime_and_sources_after_probes(self):
        self.create()

        def mutate(*args):
            (self.destination / "owned.txt").write_text("changed by probe")

        with patch.object(runtime, "health", side_effect=mutate):
            with self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.doctor(self.destination, self.plugin)

    def test_clean_health_probe_rejects_nonempty_diagnostics(self):
        binary = self.destination / "bin"
        binary.mkdir(parents=True)
        (binary / "python").symlink_to(Path(sys.executable).resolve())
        responses = [
            subprocess.CompletedProcess([], 0, b"0.1.9\n", b""),
            subprocess.CompletedProcess([], 0, b'{"continue":true}', b"unexpected diagnostic"),
        ]
        with patch.object(runtime, "run_local", side_effect=responses):
            with self.assertRaises(runtime.RuntimeErrorSafe):
                runtime.health(self.destination, self.plugin)

    def test_deep_ownership_json_fails_safely(self):
        self.create()
        record = self.destination / runtime.RECORD
        original = record.read_bytes()
        record.write_bytes(b"[" * 2000 + b"]" * 2000)
        with self.assertRaises(runtime.RuntimeErrorSafe):
            runtime.load_record(self.destination)
        record.write_bytes(original)
        runtime.remove(self.destination, self.plugin)


if __name__ == "__main__":
    unittest.main()
