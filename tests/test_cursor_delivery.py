"""Standalone delivery integrity and helper operations in unopened fixtures."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cursor_delivery", ROOT / "scripts/cursor_delivery.py"
)
assert SPEC and SPEC.loader
delivery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delivery)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gt-helper-delivery-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "maintainer source"
        for name, original in delivery.SOURCE_FILES.items():
            target = self.source / original
            target.parent.mkdir(parents=True, exist_ok=True)
            if name in ("README.md", "SUPPORT.md"):
                target.write_text("Synthetic delivery documentation fixture.\n")
            else:
                shutil.copyfile(ROOT / original, target)
        native = delivery.native.build(ROOT, self.root / "native")
        self.native = Path(native["archive"])
        self.assertEqual(native["sha256"], delivery.NATIVE_SHA256)

    def build(self, name="delivery"):
        result = delivery.build(self.source, self.root / name, self.native, delivery.NATIVE_SHA256)
        return Path(result["archive"]), result["sha256"]

    def rewrite(self, archive, change):
        with zipfile.ZipFile(archive) as packed:
            entries = [(item, packed.read(item)) for item in packed.infolist()]
        buffer = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(buffer, "w") as packed:
                for item, data in change(entries):
                    packed.writestr(item, data)
        path = self.root / "changed.zip"
        path.write_bytes(buffer.getvalue())
        return path, delivery.digest(buffer.getvalue())

    def test_reproducible_exact_closure_and_native_identity(self):
        first, checksum = self.build()
        second, repeated = self.build("again")
        self.assertEqual(checksum, repeated)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        files = delivery.verify(first, checksum)
        self.assertEqual(set(files), {*delivery.PAYLOAD_FILES, delivery.MANIFEST})
        self.assertEqual(len(files), 10)
        self.assertEqual(files[delivery.NATIVE_PATH], self.native.read_bytes())
        for name, original in delivery.SOURCE_FILES.items():
            self.assertEqual(files[name], (self.source / original).read_bytes())

    def test_delivery_identity_binds_preview_three_and_existing_sdk_runtime(self):
        archive, checksum = self.build()
        files = delivery.verify(archive, checksum)
        record = json.loads(files[delivery.MANIFEST])
        self.assertEqual(record["version"], "0.1.0-preview.3")
        self.assertEqual(record["native"]["version"], "0.1.0-preview.3")
        self.assertEqual(record["native"]["sdk_version"], "0.1.9")
        self.assertEqual(
            record["native"]["path"],
            "artifacts/guardtrellis-cursor-0.1.0-preview.3-advisory.zip",
        )
        self.assertNotIn("artifacts/guardtrellis-cursor-0.1.0-preview.1-advisory.zip", files)
        native = delivery.native.verify(self.native, delivery.NATIVE_SHA256)
        self.assertIn(b'TAG = "0.1.0-preview.1-sdk0.1.9"', native["scripts/runtime_setup.py"])
        self.assertEqual(record["native"]["sha256"], delivery.digest(files[delivery.NATIVE_PATH]))

    def test_extracted_helper_full_lifecycle_from_unrelated_cwd(self):
        archive, checksum = self.build()
        extracted = self.root / "extracted helper with spaces"
        delivery.extract(archive, checksum, extracted)
        workspace = self.root / "unopened workspace"
        workspace.mkdir()
        config = workspace / ".cursor/hooks.json"
        config.parent.mkdir()
        foreign = {
            "version": 1,
            "hooks": {
                "afterFileEdit": [{"command": "/usr/bin/true", "note": "private fixture canary"}]
            },
        }
        config.write_text(json.dumps(foreign))
        original = config.read_bytes()
        runtime = self.root / "external runtime"
        runtime.mkdir()
        sentinel = runtime / "keep.txt"
        sentinel.write_text("keep")
        unrelated = self.root / "unrelated working directory"
        unrelated.mkdir()
        python = str(Path(sys.executable).resolve())
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for name in ("PYTHONPATH", "PYTHONHOME", "UV_PROJECT", "UV_PROJECT_ENVIRONMENT"):
            env.pop(name, None)

        def run(script, *args, expected=0):
            result = subprocess.run(
                [python, "-I", "-B", str(extracted / "scripts" / script), *args],
                cwd=unrelated,
                env=env,
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, expected, result.stderr)
            return json.loads(result.stdout)

        self.assertTrue(
            run("cursor_delivery.py", "verify", str(archive), "--sha256", checksum)["verified"]
        )
        common = (
            "--workspace",
            str(workspace),
            "--archive",
            str(extracted / delivery.NATIVE_PATH),
            "--sha256",
            delivery.NATIVE_SHA256,
            "--python",
            python,
            "--runtime",
            str(runtime),
        )
        plan = run("cursor_workspace.py", "plan", *common)
        self.assertEqual(plan["status"], "planned")
        self.assertNotIn("private fixture canary", json.dumps(plan))
        self.assertEqual(config.read_bytes(), original)
        self.assertEqual(
            run("cursor_workspace.py", "install", *common)["status"], "configuration_staged"
        )
        health = run("cursor_workspace.py", "health", "--workspace", str(workspace))
        self.assertEqual(health["native_activation"], "not_observed")
        self.assertEqual(health["runtime_check"]["status"], "not_requested")
        unavailable = run(
            "cursor_workspace.py",
            "health",
            "--workspace",
            str(workspace),
            "--check-runtime",
            expected=1,
        )
        self.assertEqual(unavailable["runtime_check"]["status"], "unavailable")
        self.assertEqual(
            run("cursor_workspace.py", "remove", "--workspace", str(workspace))["status"],
            "configuration_removed",
        )
        self.assertFalse((workspace / ".guardtrellis-cursor").exists())
        self.assertEqual(json.loads(config.read_bytes()), foreign)
        self.assertEqual(sentinel.read_text(), "keep")

    def test_bad_checksum_and_existing_destinations_never_write(self):
        archive, checksum = self.build()
        destination = self.root / "never-created"
        for invalid in ("", "a", "0" * 64):
            with self.subTest(checksum=invalid), self.assertRaises(delivery.DeliveryError):
                delivery.extract(archive, invalid, destination)
            self.assertFalse(destination.exists())
        destination.mkdir()
        (destination / "keep").write_text("user-owned")
        with self.assertRaises(delivery.DeliveryError):
            delivery.extract(archive, checksum, destination)
        self.assertEqual((destination / "keep").read_text(), "user-owned")

    def test_missing_or_linked_source_and_wrong_native_fail_before_output(self):
        target = self.source / delivery.SOURCE_FILES["scripts/cursor_workspace.py"]
        original = target.read_bytes()
        target.unlink()
        with self.assertRaises(delivery.DeliveryError):
            self.build("missing")
        outside = self.root / "outside.py"
        outside.write_bytes(original)
        target.symlink_to(outside)
        with self.assertRaises(delivery.DeliveryError):
            self.build("linked")
        target.unlink()
        target.write_bytes(original)
        enforcing = delivery.native.build(ROOT, self.root / "enforcing", "enforce-secrets-v1")
        with self.assertRaises(delivery.DeliveryError):
            delivery.build(
                self.source,
                self.root / "wrong-native",
                Path(enforcing["archive"]),
                delivery.NATIVE_SHA256,
            )
        for name in ("missing", "linked", "wrong-native"):
            self.assertFalse((self.root / name).exists())

    def test_private_repo_and_mcp_files_are_not_selected(self):
        for name in ("services/private.env", "docs/private-report.md", "mcp.json", ".git/config"):
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("synthetic private source")
        archive, checksum = self.build()
        self.assertFalse(
            any(
                name.startswith(("services/", "docs/", ".git/", "mcp"))
                for name in delivery.verify(archive, checksum)
            )
        )

    def test_unsafe_duplicate_case_extra_and_missing_archive_paths_are_rejected(self):
        archive, checksum = self.build()
        for name in (
            "../escape",
            "/absolute",
            "C:/drive",
            "a\\escape",
            "a//escape",
            "README.md",
            "readme.md",
            "mcp.json",
        ):
            changed, value = self.rewrite(
                archive,
                lambda entries, name=name: entries + [(zipfile.ZipInfo(name), b"synthetic")],
            )
            with (
                self.subTest(name=name),
                self.assertRaises((delivery.DeliveryError, delivery.native.ReleaseError)),
            ):
                delivery.verify(changed, value)
        changed, value = self.rewrite(archive, lambda entries: entries[1:])
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify(changed, value)

    def test_changed_contents_manifest_and_native_record_are_rejected(self):
        archive, checksum = self.build()
        changed, value = self.rewrite(
            archive,
            lambda entries: [
                (item, data + b"changed" if item.filename == "SUPPORT.md" else data)
                for item, data in entries
            ],
        )
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify(changed, value)
        for field, value in (
            ("format", True),
            ("version", "0.1.0-preview.1"),
            ("native", {"profile": "enforce-secrets-v1"}),
            ("files", {}),
        ):

            def mutate(entries, field=field, value=value):
                result = []
                for item, data in entries:
                    if item.filename == delivery.MANIFEST:
                        record = json.loads(data)
                        record[field] = value
                        data = json.dumps(record).encode()
                    result.append((item, data))
                return result

            changed, digest = self.rewrite(archive, mutate)
            with self.subTest(field=field), self.assertRaises(delivery.DeliveryError):
                delivery.verify(changed, digest)

    def test_links_devices_compression_and_bounds_are_rejected(self):
        archive, checksum = self.build()
        for kind in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFIFO):

            def mutate(entries, kind=kind):
                entries[0][0].external_attr = (kind | 0o644) << 16
                return entries

            changed, value = self.rewrite(archive, mutate)
            with self.subTest(kind=kind), self.assertRaises(delivery.DeliveryError):
                delivery.verify(changed, value)

        def compressed(entries):
            entries[0][0].compress_type = zipfile.ZIP_DEFLATED
            return entries

        changed, value = self.rewrite(archive, compressed)
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify(changed, value)
        with patch.object(delivery, "MAX_BYTES", 100):
            with self.assertRaises(delivery.DeliveryError):
                self.build("bounded")
        self.assertFalse((self.root / "bounded").exists())

    def test_duplicate_and_non_object_manifest_metadata_are_rejected(self):
        archive, checksum = self.build()
        for replacement in (b'{"format":1,"format":1}', b"[]", b'{"format":NaN}'):
            changed, value = self.rewrite(
                archive,
                lambda entries, replacement=replacement: [
                    (item, replacement if item.filename == delivery.MANIFEST else data)
                    for item, data in entries
                ],
            )
            with (
                self.subTest(replacement=replacement),
                self.assertRaises((delivery.DeliveryError, delivery.native.ReleaseError)),
            ):
                delivery.extract(changed, value, self.root / "never-created")
            self.assertFalse((self.root / "never-created").exists())

    def test_parent_links_and_post_creation_swap_preserve_outside_sentinel(self):
        archive, checksum = self.build()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "keep").write_text("outside sentinel")
        alias = self.root / "alias"
        alias.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(delivery.DeliveryError):
            delivery.extract(archive, checksum, alias / "new")
        destination = self.root / "fresh"
        original = delivery.os.mkdir
        swapped = False

        def swap(name, *args, **kwargs):
            nonlocal swapped
            result = original(name, *args, **kwargs)
            if name == destination.name and kwargs.get("dir_fd") is not None and not swapped:
                swapped = True
                destination.rename(self.root / "retired")
                destination.symlink_to(outside, target_is_directory=True)
            return result

        with patch.object(delivery.os, "mkdir", side_effect=swap):
            with self.assertRaises(OSError):
                delivery.extract(archive, checksum, destination)
        self.assertTrue(swapped)
        self.assertEqual({path.name for path in outside.iterdir()}, {"keep"})
        self.assertEqual((outside / "keep").read_text(), "outside sentinel")


if __name__ == "__main__":
    unittest.main()
