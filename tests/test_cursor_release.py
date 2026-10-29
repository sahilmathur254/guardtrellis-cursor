"""Native package integrity and extraction checks in disposable directories."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import stat
import tempfile
import unittest
import warnings
import zipfile
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cursor_release", ROOT / "scripts/cursor_release.py")
assert SPEC and SPEC.loader
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class NativeReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gt-cursor-package-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source with spaces"
        for name in release.SOURCE_MAP.values():
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def build(self, profile="advisory", output="output"):
        result = release.build(self.source, self.root / output, profile)
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
        return path, release.digest(buffer.getvalue())

    def test_profiles_are_deterministic_distinct_explicit_and_bounded(self):
        hashes = []
        for profile in release.PROFILES:
            first, checksum = self.build(profile, profile + "-a")
            second, repeated = self.build(profile, profile + "-b")
            self.assertEqual(checksum, repeated)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            files = release.verify(first, checksum)
            self.assertEqual(set(files), {*release.SOURCE_MAP, release.MANIFEST})
            hooks = json.loads(files["hooks/hooks.json"])
            definition = hooks["hooks"]["beforeSubmitPrompt"][0]
            self.assertIs(definition["failClosed"], profile != "advisory")
            self.assertEqual(definition["timeout"], 2)
            if profile == "advisory":
                self.assertEqual(definition["command"], "/bin/sh ./scripts/guardtrellis.sh hook")
            else:
                self.assertIn("--profile " + profile, definition["command"])
            hashes.append(checksum)
        self.assertNotEqual(*hashes)

    def test_unlisted_private_data_and_mcp_are_excluded(self):
        for name in ("mcp.json", ".env", "private/customer.txt"):
            target = self.source / release.TEMPLATE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("synthetic private canary")
        archive, checksum = self.build()
        files = release.verify(archive, checksum)
        self.assertFalse(
            any(name.startswith(("services/", "mcp", ".env", "private/")) for name in files)
        )

    def test_existing_runtime_sources_are_copied_exactly(self):
        archive, checksum = self.build()
        files = release.verify(archive, checksum)
        for target, original in release.SOURCE_MAP.items():
            if target.startswith(("adapters/", "runtime/")):
                self.assertEqual(files[target], (self.source / original).read_bytes())

    def test_native_public_docs_do_not_depend_on_shared_skills_copy(self):
        first, checksum = self.build(output="native-docs-before")
        for name in ("PRIVACY.md", "SUPPORT.md", "NOTICE"):
            self.assertEqual(release.SOURCE_MAP[name], f"{release.TEMPLATE}/{name}")
            shared = self.source / release.EXISTING / name
            shared.parent.mkdir(parents=True, exist_ok=True)
            shared.write_text("Unrelated shared-skills documentation canary.\n")
        second, repeated = self.build(output="native-docs-after")
        self.assertEqual(checksum, repeated)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        files = release.verify(second, repeated)
        for name in ("PRIVACY.md", "SUPPORT.md", "NOTICE"):
            self.assertEqual(files[name], (self.source / release.SOURCE_MAP[name]).read_bytes())
            self.assertNotIn(b"shared-skills documentation canary", files[name])

    def test_new_source_identity_keeps_existing_runtime_identity(self):
        archive, checksum = self.build()
        files = release.verify(archive, checksum)
        self.assertEqual(release.VERSION, "0.1.0-preview.3")
        self.assertEqual(len(files), 23)
        self.assertEqual(
            json.loads(files[".cursor-plugin/plugin.json"])["version"], release.VERSION
        )
        self.assertIn(b'TAG = "0.1.0-preview.1-sdk0.1.9"', files["scripts/runtime_setup.py"])
        self.assertIn(b"gt_cursor_tag=0.1.0-preview.1-sdk0.1.9", files["scripts/guardtrellis.sh"])
        stale = {name: files[name] for name in release.SOURCE_MAP}
        metadata = json.loads(stale[".cursor-plugin/plugin.json"])
        metadata["version"] = "0.1.0-preview.2"
        stale[".cursor-plugin/plugin.json"] = json.dumps(metadata).encode()
        with self.assertRaises(release.ReleaseError):
            release.validate(stale, "advisory")

    def test_safe_extraction_and_moved_plugin_preserve_sources(self):
        archive, checksum = self.build()
        destination = self.root / "extracted plugin with spaces"
        result = release.extract(archive, checksum, destination)
        self.assertEqual(result["hook_activation"], "not_performed")
        moved = self.root / "moved plugin"
        destination.rename(moved)
        self.assertEqual(
            (moved / "runtime/uv.lock").read_bytes(),
            (self.source / release.SOURCE_MAP["runtime/uv.lock"]).read_bytes(),
        )
        with self.assertRaises(release.ReleaseError):
            release.extract(archive, checksum, moved)

    def test_bad_checksum_fails_before_extraction(self):
        archive, checksum = self.build()
        for value in ("", "a", "0" * 64):
            with self.subTest(value=value), self.assertRaises(release.ReleaseError):
                release.extract(archive, value, self.root / "never-created")
        self.assertFalse((self.root / "never-created").exists())

    def test_source_and_archive_symlinks_are_rejected(self):
        archive, checksum = self.build()
        alias = self.root / "linked.zip"
        alias.symlink_to(archive)
        with self.assertRaises(release.ReleaseError):
            release.verify(alias, checksum)
        target = self.source / release.SOURCE_MAP["README.md"]
        original = target.read_bytes()
        target.unlink()
        external = self.root / "external.md"
        external.write_bytes(original)
        target.symlink_to(external)
        with self.assertRaises(release.ReleaseError):
            self.build(output="must-not-exist")
        self.assertFalse((self.root / "must-not-exist").exists())

    def test_unsafe_duplicate_extra_and_case_paths_are_rejected(self):
        archive, checksum = self.build()
        for name in (
            "../escape",
            "/absolute",
            "C:/drive",
            "x\\escape",
            "x//escape",
            "x/./escape",
            "mcp.json",
            "readme.md",
            "README.md",
        ):
            with self.subTest(name=name):
                changed, digest = self.rewrite(
                    archive,
                    lambda entries, name=name: entries + [(zipfile.ZipInfo(name), b"synthetic")],
                )
                with self.assertRaises(release.ReleaseError):
                    release.verify(changed, digest)

    def test_link_device_compression_and_tamper_are_rejected(self):
        archive, checksum = self.build()
        for kind in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFIFO, stat.S_IFDIR):

            def mutate(entries, kind=kind):
                entries[0][0].external_attr = (kind | 0o644) << 16
                return entries

            with self.subTest(kind=kind):
                changed, value = self.rewrite(archive, mutate)
                with self.assertRaises(release.ReleaseError):
                    release.verify(changed, value)

        def compressed(entries):
            entries[0][0].compress_type = zipfile.ZIP_DEFLATED
            return entries

        changed, value = self.rewrite(archive, compressed)
        with self.assertRaises(release.ReleaseError):
            release.verify(changed, value)
        changed, value = self.rewrite(
            archive,
            lambda entries: [
                (item, data + b"tampered" if item.filename == "README.md" else data)
                for item, data in entries
            ],
        )
        with self.assertRaises(release.ReleaseError):
            release.verify(changed, value)

    def test_malformed_metadata_duplicate_keys_mcp_and_stale_pin_rejected(self):
        for target, value in (
            (".cursor-plugin/plugin.json", b'{"name":"guardtrellis-cursor","name":"other"}'),
            ("runtime/pyproject.toml", b"invalid ["),
            ("runtime/uv.lock", b'[[package]]\nname="guardtrellis"\nversion="0.1.6"\n'),
        ):
            path = self.source / release.SOURCE_MAP[target]
            original = path.read_bytes()
            with self.subTest(target=target):
                path.write_bytes(value)
                with self.assertRaises(release.ReleaseError):
                    self.build(output="invalid-" + target.replace("/", "-"))
                path.write_bytes(original)
        path = self.source / release.SOURCE_MAP[".cursor-plugin/plugin.json"]
        metadata = json.loads(path.read_bytes())
        metadata["mcpServers"] = {}
        path.write_text(json.dumps(metadata))
        with self.assertRaises(release.ReleaseError):
            self.build(output="mcp-rejected")

    def test_invalid_manifest_core_types_and_hook_booleans_are_rejected(self):
        archive, checksum = self.build()
        original = release.verify(archive, checksum)
        original.pop(release.MANIFEST)
        for key, value in (
            ("author", []),
            ("keywords", {}),
            ("description", None),
            ("hooks", []),
            ("license", False),
        ):
            with self.subTest(key=key):
                files = original.copy()
                metadata = json.loads(files[".cursor-plugin/plugin.json"])
                metadata[key] = value
                files[".cursor-plugin/plugin.json"] = json.dumps(metadata).encode()
                with self.assertRaises(release.ReleaseError):
                    release.validate(files, "advisory")
        files = original.copy()
        config = json.loads(files["hooks/hooks.json"])
        config["hooks"]["beforeSubmitPrompt"][0]["failClosed"] = 0
        files["hooks/hooks.json"] = json.dumps(config).encode()
        with self.assertRaises(release.ReleaseError):
            release.validate(files, "advisory")

    def catalog(self):
        value = {
            "name": release.CATALOG_NAME,
            "owner": {"name": "Sahil Mathur"},
            "metadata": {"description": "Local Cursor integration", "version": release.VERSION},
            "plugins": [{"name": release.NAME, "source": "./" + release.GENERATED}],
        }
        path = self.source / release.CATALOG
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path, value

    def indexed(self):
        release.export(self.source)
        self.catalog()
        return self.source / release.GENERATED

    def test_advisory_export_is_exact_archive_content_and_catalog_is_separate(self):
        result = release.export(self.source)
        self.assertEqual(result["profile"], "advisory")
        self.assertEqual(result["files"], 23)
        self.assertEqual(result["catalog"], "not_written")
        self.assertFalse((self.source / release.CATALOG).exists())
        archive, checksum = self.build()
        files = release.verify(archive, checksum)
        generated = self.source / release.GENERATED
        self.assertEqual(
            {
                path.relative_to(generated).as_posix(): path.read_bytes()
                for path in generated.rglob("*")
                if path.is_file()
            },
            files,
        )
        self.assertTrue(release.check_export(self.source, check_catalog=False)["verified"])
        with self.assertRaises(release.ExportDriftError) as missing:
            release.check_export(self.source)
        self.assertEqual(missing.exception.differences["catalog"], ["missing_catalog"])
        self.catalog()
        self.assertEqual(release.check_export(self.source)["catalog"], "checked")

    def test_existing_export_is_never_overwritten_even_if_intact_or_unrelated(self):
        generated = self.indexed()
        before = (generated / "README.md").read_bytes()
        for extra in (False, True):
            if extra:
                (generated / "unrelated.txt").write_text("user-owned data")
            with self.subTest(extra=extra), self.assertRaises(release.ReleaseError):
                release.export(self.source)
            self.assertEqual((generated / "README.md").read_bytes(), before)
        self.assertEqual((generated / "unrelated.txt").read_text(), "user-owned data")

    def test_generated_changes_are_not_authoritative_and_are_not_repaired(self):
        generated = self.indexed()
        original, checksum = self.build(output="before")
        modified = generated / "adapters/common/prompt_runtime.py"
        modified.write_text("synthetic changed generated implementation")
        (generated / release.MANIFEST).write_text("{}")
        with self.assertRaises(release.ExportDriftError) as drift:
            release.check_export(self.source)
        self.assertEqual(
            set(drift.exception.differences["modified"]),
            {"adapters/common/prompt_runtime.py", release.MANIFEST},
        )
        self.assertEqual(modified.read_text(), "synthetic changed generated implementation")
        rebuilt, repeated = self.build(output="after")
        self.assertEqual(checksum, repeated)
        self.assertEqual(original.read_bytes(), rebuilt.read_bytes())

    def test_missing_extra_shadow_components_and_empty_directories_are_rejected(self):
        generated = self.indexed()
        (generated / "runtime/uv.lock").unlink()
        for name in ("mcp.json", ".env", "SKILL.md", "hooks/shadow.json"):
            (generated / name).write_text("synthetic extra")
        (generated / "unexpected-empty").mkdir()
        with self.assertRaises(release.ExportDriftError) as drift:
            release.check_export(self.source)
        self.assertEqual(drift.exception.differences["missing"], ["runtime/uv.lock"])
        self.assertEqual(
            set(drift.exception.differences["extra"]),
            {"mcp.json", ".env", "SKILL.md", "hooks/shadow.json", "unexpected-empty/"},
        )

    def test_linked_generated_files_root_and_catalog_are_not_followed(self):
        generated = self.indexed()
        outside = self.root / "outside.txt"
        outside.write_text("synthetic private canary")
        (generated / "README.md").unlink()
        (generated / "README.md").symlink_to(outside)
        with self.assertRaises(release.ExportDriftError) as drift:
            release.check_export(self.source)
        self.assertIn("README.md", drift.exception.differences["unsafe"])
        shutil.rmtree(generated)
        generated.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(release.ExportDriftError) as drift:
            release.check_export(self.source)
        self.assertIn(release.GENERATED, drift.exception.differences["unsafe"])
        generated.unlink()
        release.export(self.source)
        catalog = self.source / release.CATALOG
        catalog.unlink()
        catalog.symlink_to(outside)
        with self.assertRaises(release.ExportDriftError) as drift:
            release.check_export(self.source)
        self.assertEqual(drift.exception.differences["catalog"], ["linked_catalog_path"])
        self.assertEqual(outside.read_text(), "synthetic private canary")

    def test_case_variant_and_case_collision_cannot_replace_a_canonical_path(self):
        generated = self.indexed()
        (generated / "README.md").rename(generated / "readme.md")
        with self.assertRaises(release.ExportDriftError):
            release.check_export(self.source)
        (generated / "README.md").write_text("synthetic second case variant")
        with self.assertRaises(release.ExportDriftError) as drift:
            release.check_export(self.source)
        names = {path.name for path in generated.iterdir()}
        if {"README.md", "readme.md"} <= names:
            self.assertEqual(
                set(drift.exception.differences["case_collisions"]), {"README.md", "readme.md"}
            )

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires a POSIX FIFO")
    def test_special_file_is_rejected_without_reading_it(self):
        generated = self.indexed()
        os.mkfifo(generated / "unexpected.pipe")
        with self.assertRaises(release.ExportDriftError) as drift:
            release.check_export(self.source)
        self.assertIn("unexpected.pipe", drift.exception.differences["unsafe"])

    def test_catalog_source_escape_and_shadow_component_overrides_are_rejected(self):
        self.indexed()
        path, original = self.catalog()
        for source in (
            "../escape",
            "/absolute",
            "./plugins/other",
            "./plugins/guardtrellis-cursor/../guardtrellis-cursor",
        ):
            value = json.loads(json.dumps(original))
            value["plugins"][0]["source"] = source
            path.write_text(json.dumps(value))
            with self.subTest(source=source), self.assertRaises(release.ExportDriftError):
                release.check_export(self.source)
        for location in ("root", "metadata", "entry"):
            for component in ("mcpServers", "hooks", "commands", "skills", "variables"):
                value = json.loads(json.dumps(original))
                target = (
                    value
                    if location == "root"
                    else value["metadata"]
                    if location == "metadata"
                    else value["plugins"][0]
                )
                target[component] = "shadow"
                path.write_text(json.dumps(value))
                with (
                    self.subTest(location=location, component=component),
                    self.assertRaises(release.ExportDriftError),
                ):
                    release.check_export(self.source)

    def test_drift_cli_returns_structured_failure_and_does_not_mutate(self):
        generated = self.indexed()
        path = generated / "README.md"
        path.write_text("modified generated documentation")
        output = io.StringIO()
        with redirect_stderr(output):
            result = release.main(["check-export", "--source", str(self.source)])
        self.assertEqual(result, 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["reason"], "native_export_drift")
        self.assertEqual(report["differences"]["modified"], ["README.md"])
        self.assertEqual(path.read_text(), "modified generated documentation")

    def test_export_allows_managed_worktrees_but_refuses_normal_profiles(self):
        home = self.root / "synthetic-home"
        managed = home / ".codex/worktrees/test/repository"
        shutil.copytree(self.source, managed)
        with patch.object(release.Path, "home", return_value=home):
            with self.assertRaises(release.ReleaseError):
                release.export(managed)
            (managed / ".git").write_text("gitdir: /synthetic/managed-worktree\n")
            self.assertEqual(release.export(managed)["profile"], "advisory")
            for location in (
                ".codex/plugins/cache",
                ".claude",
                ".cursor",
                "Library/Application Support/Cursor",
            ):
                destination = home / location / "repository"
                with self.subTest(location=location), self.assertRaises(release.ReleaseError):
                    release.export(destination)
                self.assertFalse(destination.exists())
            alias = managed.parent / "profile-alias"
            alias.symlink_to(home / ".codex/plugins/cache/repository", target_is_directory=True)
            with self.assertRaises(release.ReleaseError):
                release.export(alias)
            self.assertFalse((home / ".codex/plugins").exists())


if __name__ == "__main__":
    unittest.main()
