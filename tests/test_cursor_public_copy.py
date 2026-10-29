"""Public-copy contracts bind package selection, usable commands and claim limits."""

from __future__ import annotations

import importlib.util
import re
import shlex
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


native = module("public_copy_native", ROOT / "scripts/cursor_release.py")


def shell_invocations(text):
    """Read documentation as text; do not execute shell syntax or read environment values."""
    variables = {}
    commands = []

    def resolve(value):
        for _ in range(8):
            changed = re.sub(
                r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))",
                lambda match: variables.get(match[1] or match[2], match[0]),
                value,
            )
            if changed == value:
                return value
            value = changed
        return value

    for block in re.findall(r"```(?:sh|bash|shell|zsh)\n(.*?)```", text, re.S):
        for line in block.replace("\\\n", " ").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            tokens = shlex.split(line, comments=True)
            if len(tokens) == 1 and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
                key, value = tokens[0].split("=", 1)
                variables[key] = resolve(value)
                continue
            resolved = [resolve(token) for token in tokens]
            for index, token in enumerate(resolved):
                if token.endswith(("/cursor_workspace.py", "/runtime_setup.py")):
                    commands.append((token, resolved[index + 1 :]))
    return commands


class PublicCopyTests(unittest.TestCase):
    def test_native_public_copy_builds_from_only_declared_native_inputs(self):
        with tempfile.TemporaryDirectory(prefix="gt-native-copy-") as temporary:
            work = Path(temporary).resolve()
            source = work / "source"
            for name in set(native.SOURCE_MAP.values()):
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            self.assertFalse((source / "scripts/release.py").exists())
            self.assertFalse((source / "plugins/guardtrellis/skills").exists())
            original_native = native.build(source, work / "native-before")
            original_inputs = {
                name: (source / relative).read_bytes()
                for name, relative in native.SOURCE_MAP.items()
            }
            changed_names = ("PRIVACY.md", "SUPPORT.md")
            for name in changed_names:
                with (source / native.SOURCE_MAP[name]).open("ab") as handle:
                    handle.write(b"\nSynthetic public-copy revision for packaging isolation.\n")
            revised_native = native.build(source, work / "native-after")
            self.assertNotEqual(original_native["sha256"], revised_native["sha256"])
            revised_files = native.verify(Path(revised_native["archive"]), revised_native["sha256"])
            for name, original in original_inputs.items():
                expected = (source / native.SOURCE_MAP[name]).read_bytes()
                self.assertEqual(revised_files[name], expected)
                if name in changed_names:
                    self.assertNotEqual(expected, original)
                else:
                    self.assertEqual(expected, original)

    def test_native_and_outer_notices_use_the_same_selected_native_scope(self):
        delivery = module("public_copy_delivery", ROOT / "scripts/cursor_delivery.py")
        selected = "integrations/cursor/plugin/NOTICE"
        self.assertEqual(native.SOURCE_MAP["NOTICE"], selected)
        self.assertEqual(delivery.SOURCE_FILES["NOTICE"], selected)
        notice = (ROOT / selected).read_text()
        self.assertIn("Copyright 2026 Sahil Mathur", notice)
        self.assertIn("Apache", notice)
        self.assertNotIn("THIRD_PARTY_NOTICES.md", notice)
        self.assertNotIn("skills/", notice)
        with tempfile.TemporaryDirectory(prefix="gt-native-notice-") as temporary:
            result = native.build(ROOT, Path(temporary) / "native")
            files = native.verify(Path(result["archive"]), result["sha256"])
            self.assertEqual(files["NOTICE"], notice.encode())

    def test_outer_guide_has_usable_helper_and_retained_runtime_removal_contract(self):
        text = (ROOT / "integrations/cursor/delivery/README.md").read_text()
        commands = shell_invocations(text)
        helper = [
            (i, path, args)
            for i, (path, args) in enumerate(commands)
            if path.endswith("/cursor_workspace.py")
        ]
        self.assertTrue(helper)
        self.assertEqual(
            {args[0] for _, _, args in helper}, {"plan", "install", "health", "remove"}
        )
        for _, path, args in helper:
            self.assertTrue(path.startswith("/"))
            self.assertIn("--workspace", args)
            self.assertNotIn("--dest", args)
            if args[0] in ("plan", "install"):
                self.assertTrue({"--archive", "--sha256", "--python", "--runtime"} <= set(args))
        helper_remove = next(i for i, _, args in helper if args[0] == "remove")
        runtime_remove = [
            (i, path, args)
            for i, (path, args) in enumerate(commands)
            if path.endswith("/runtime_setup.py") and args and args[0] == "remove"
        ]
        self.assertEqual(len(runtime_remove), 1)
        index, script, arguments = runtime_remove[0]
        self.assertGreater(index, helper_remove)
        self.assertIn("--dest", arguments)
        workspace = helper[0][2][helper[0][2].index("--workspace") + 1]
        self.assertFalse(script.startswith(workspace + "/"))
        self.assertNotIn(".guardtrellis-cursor/", script)

    def test_public_claims_preserve_current_identity_and_boundary_limits(self):
        for relative in (
            "integrations/cursor/plugin/README.md",
            "integrations/cursor/delivery/README.md",
        ):
            text = (ROOT / relative).read_text().lower()
            with self.subTest(relative=relative):
                self.assertIn(native.VERSION.lower(), text)
                # These are disclosure/claim invariants, not proof of host behavior.
                self.assertIn("accepted runtime", text)
                self.assertIn("documentation-only", text)
                self.assertRegex(text, r"new (?:package )?checksums")
                self.assertRegex(text, r"not (?:itself|themselves) whole-package host-tested")
                self.assertRegex(text, r"automated escape.{0,30}empty")
                for term in ("trust", "failure", "bypass", "downstream", "unverified"):
                    self.assertIn(term, text)
                for term in ("preview.3", "cancel", "owner-assisted", "prior"):
                    self.assertIn(term, text)
                self.assertIn("0.1.0-preview.1-sdk0.1.9", text)
                self.assertRegex(text, r"prompt hook does not rewrite prompts")
                self.assertIn("advisory", text)
                for term in ("attachments", "history", "mcp", "inline", "other agents"):
                    self.assertIn(term, text)
        privacy = (ROOT / "integrations/cursor/plugin/PRIVACY.md").read_text()
        self.assertIn("checks only its submitted prompt", privacy)
        self.assertIn("workspaceOpen", privacy)
        for relative in (
            "integrations/cursor/plugin/SUPPORT.md",
            "integrations/cursor/delivery/SUPPORT.md",
        ):
            text = (ROOT / relative).read_text().lower()
            with self.subTest(relative=relative):
                self.assertRegex(text, r"metadata[- ]only|reviewed metadata template")
                self.assertIn("raw prompts", text)

    def test_prefill_guides_show_complete_explicit_target_without_executing_it(self):
        required = {"--user-data-dir", "--extensions-dir", "--cursor-profile"}
        for relative in (
            "integrations/cursor/plugin/README.md",
            "integrations/cursor/delivery/README.md",
            "integrations/cursor/plugin/commands/guardtrellis-prepare.md",
        ):
            text = (ROOT / relative).read_text()
            invocations = []
            for block in re.findall(r"```sh\n(.*?)```", text, re.S):
                for line in block.replace("\\\n", " ").splitlines():
                    tokens = shlex.split(line, comments=True)
                    for index, token in enumerate(tokens):
                        if token.endswith("/guardtrellis.sh"):
                            invocations.append(tokens[index + 1 :])
            with self.subTest(relative=relative):
                self.assertTrue(
                    any(
                        args and args[0] == "prepare" and "--open" not in args
                        for args in invocations
                    )
                )
                opened = [args for args in invocations if "--open" in args]
                self.assertEqual(len(opened), 1)
                self.assertTrue(required <= set(opened[0]))
                for flag in required:
                    self.assertLess(opened[0].index(flag) + 1, len(opened[0]))
                lower = text.lower()
                for term in ("no", "fallback", "retry", "handoff", "cancel", "workspace/window"):
                    self.assertIn(term, lower)
                self.assertIn("https://cursor.com/docs/reference/deeplinks", text)

    def test_ci_requires_deliberate_dispatch_and_keeps_bounded_offline_checks(self):
        text = (ROOT / ".github/workflows/cursor-native.yml").read_text()
        events = text.split("on:\n", 1)[1].split("permissions:\n", 1)[0]
        self.assertEqual(re.findall(r"^  ([A-Za-z_]+):", events, re.M), ["workflow_dispatch"])
        self.assertRegex(text, r"permissions:\n  contents: read\n")
        self.assertIn("runs-on: macos-latest", text)
        self.assertIn("python-version: '3.12'", text)
        self.assertIn("version: '0.8.17'", text)
        actions = re.findall(r"uses: ([^\s]+)", text)
        self.assertEqual(len(actions), 3)
        for action in actions:
            self.assertRegex(action, r"^[^@]+@[0-9a-f]{40}$")
        phases = re.findall(r"scripts/check_cursor_release\.py --phase ([a-z]+)", text)
        self.assertEqual(phases, ["tests", "static", "artifacts", "lifecycle"])
        self.assertIn("git diff --exit-code", text)
        self.assertNotRegex(text, r"permissions:[\s\S]*?contents: write")


if __name__ == "__main__":
    unittest.main()
