"""Offline native Cursor launcher contracts; never load a plugin or open an app."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "plugin"
TAG = "0.1.0-preview.1-sdk0.1.9"
MARKER = ".guardtrellis-cursor-runtime-v1"


class TemplateTests(unittest.TestCase):
    def test_native_manifest_has_no_mcp_or_automatic_setup(self) -> None:
        manifest = json.loads((SOURCE / ".cursor-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "guardtrellis-cursor")
        self.assertEqual(manifest["version"], "0.1.0-preview.3")
        self.assertEqual(manifest["hooks"], "hooks/hooks.json")
        self.assertEqual(manifest["commands"], "commands")
        self.assertNotIn("mcpServers", manifest)
        config = json.loads((SOURCE / manifest["hooks"]).read_text())
        self.assertEqual(
            config,
            {
                "version": 1,
                "hooks": {
                    "beforeSubmitPrompt": [
                        {
                            "command": "/bin/sh ./scripts/guardtrellis.sh hook",
                            "timeout": 2,
                            "failClosed": False,
                        }
                    ]
                },
            },
        )

    def test_commands_are_terminal_guides_not_private_chat_inputs(self) -> None:
        commands = sorted((SOURCE / "commands").glob("*.md"))
        self.assertEqual(len(commands), 4)
        for command in commands:
            text = command.read_text()
            self.assertTrue(text.startswith("---\nname: guardtrellis-"))
            self.assertIn("Terminal", text)
        prepare = (SOURCE / "commands/guardtrellis-prepare.md").read_text()
        self.assertRegex(prepare.lower(), r"do not (?:request|ask for) private text in chat")
        self.assertRegex(prepare.lower(), r"never (?:presses send|sends)")
        self.assertIn("[PII] [PII]", prepare)


@unittest.skipUnless(sys.platform == "darwin", "macOS-only native candidate")
class LauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gt-cursor-launcher-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.plugin = self.root / "plugin with spaces"
        shutil.copytree(SOURCE, self.plugin)
        self.launcher = self.plugin / "scripts/guardtrellis.sh"
        adapters = self.plugin / "adapters/cursor"
        adapters.mkdir(parents=True)
        for filename in ("prompt_check.py", "prepare_prompt.py"):
            (adapters / filename).write_text("# An inert path target for the fake interpreter.\n")
        self.runtime = self.root / "external runtime"
        (self.runtime / "bin").mkdir(parents=True)
        self.marker = self.runtime / MARKER
        self.marker.write_text(TAG + "\n")
        self.python = self.runtime / "bin/python"
        self.python.write_text(
            "#!/bin/sh\n"
            'printf "%s\\n" "$@" > "$GT_CURSOR_TEST_ARGS"\n'
            '/bin/cat > "$GT_CURSOR_TEST_INPUT"\n'
            'printf "%s" "$GT_CURSOR_TEST_OUTPUT"\n'
            'printf "%s" "$GT_CURSOR_TEST_DIAGNOSTIC" >&2\n'
            'exit "$GT_CURSOR_TEST_EXIT"\n'
        )
        self.python.chmod(0o700)
        self.env = dict(os.environ)
        self.env.update(
            GUARDTRELLIS_CURSOR_RUNTIME=str(self.runtime),
            GT_CURSOR_TEST_ARGS=str(self.root / "arguments.txt"),
            GT_CURSOR_TEST_INPUT=str(self.root / "input.bin"),
            GT_CURSOR_TEST_OUTPUT='{"continue":true}\n',
            GT_CURSOR_TEST_DIAGNOSTIC='{"check_status":"checked"}\n',
            GT_CURSOR_TEST_EXIT="0",
        )
        self.cwd = self.root / "unrelated workspace with spaces"
        self.cwd.mkdir()

    def run_launcher(
        self, *arguments: str, raw: bytes = b'{"prompt":"Synthetic fixture"}'
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["/bin/sh", str(self.launcher), *arguments],
            input=raw,
            capture_output=True,
            cwd=self.cwd,
            env=self.env,
            timeout=5,
            check=False,
        )

    def assert_unavailable(
        self,
        result: subprocess.CompletedProcess[bytes],
        *,
        blocked: bool = False,
        prepare: bool = False,
        reason: str = "runtime_unavailable",
    ) -> None:
        self.assertEqual(result.returncode, 1 if prepare else 0)
        if prepare:
            self.assertEqual(result.stdout, b"")
        else:
            response = json.loads(result.stdout)
            self.assertIs(response["continue"], not blocked)
            if blocked:
                self.assertEqual(
                    response["user_message"],
                    "GuardTrellis could not check this prompt. "
                    "This configured check requests cancellation.",
                )
        self.assertEqual(
            json.loads(result.stderr),
            {
                "component": "guardtrellis_cursor_launcher",
                "check_status": "unavailable",
                "reason_code": reason,
            },
        )
        self.assertFalse((self.root / "arguments.txt").exists())
        self.assertNotIn(b"Synthetic fixture", result.stdout + result.stderr)
        self.assertNotIn(str(self.root).encode(), result.stdout + result.stderr)

    def test_advisory_uses_absolute_interpreter_and_own_bundled_path(self) -> None:
        raw = b'{"prompt":"Synthetic fixture with spaces"}'
        result = self.run_launcher("hook", raw=raw)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, self.env["GT_CURSOR_TEST_OUTPUT"].encode())
        self.assertEqual((self.root / "input.bin").read_bytes(), raw)
        self.assertEqual(
            (self.root / "arguments.txt").read_text().splitlines(),
            [
                "-I",
                "-B",
                str(self.plugin / "adapters/cursor/prompt_check.py"),
                "--profile",
                "advisory",
                "--diagnostics",
                "findings",
            ],
        )

    def test_explicit_enforcing_profile_is_forwarded(self) -> None:
        self.run_launcher("hook", "--profile", "enforce-secrets-v1")
        args = (self.root / "arguments.txt").read_text().splitlines()
        self.assertEqual(
            args[-4:], ["--profile", "enforce-secrets-v1", "--diagnostics", "findings"]
        )

    def test_prepare_without_open_passes_only_plaintext_stdin(self) -> None:
        self.env["GT_CURSOR_TEST_OUTPUT"] = "Mira [PII] [PII]."
        raw = b"Mira mira@example.org +12025550123."
        result = self.run_launcher("prepare", raw=raw)
        self.assertEqual(result.stdout, b"Mira [PII] [PII].")
        self.assertEqual((self.root / "input.bin").read_bytes(), raw)
        self.assertEqual(
            (self.root / "arguments.txt").read_text().splitlines(),
            [
                "-I",
                "-B",
                str(self.plugin / "adapters/cursor/prepare_prompt.py"),
            ],
        )

    def test_prepare_open_is_only_an_explicit_forwarded_option(self) -> None:
        self.env["GT_CURSOR_TEST_OUTPUT"] = ""
        result = self.run_launcher("prepare", "--open", raw=b"Synthetic fixture")
        self.assertEqual(result.stdout, b"")
        self.assertEqual((self.root / "arguments.txt").read_text().splitlines()[-1], "--open")

    def test_missing_marker_advisory_stays_unavailable_and_continues(self) -> None:
        self.marker.unlink()
        self.assert_unavailable(self.run_launcher("hook"))

    def test_missing_marker_enforcing_requests_cancellation(self) -> None:
        self.marker.unlink()
        self.assert_unavailable(
            self.run_launcher("hook", "--profile", "enforce-secrets-v1"), blocked=True
        )

    def test_missing_marker_prepare_withholds_everything(self) -> None:
        self.marker.unlink()
        self.assert_unavailable(self.run_launcher("prepare", "--open"), prepare=True)

    def test_wrong_marker_is_rejected(self) -> None:
        self.marker.write_text("0.1.0-preview.1-sdk0.1.6\n")
        self.assert_unavailable(self.run_launcher("hook"))

    def test_extra_marker_lines_are_rejected(self) -> None:
        self.marker.write_text(TAG + "\n\n")
        self.assert_unavailable(self.run_launcher("hook"))

    def test_trailing_nul_marker_is_rejected_byte_for_byte(self) -> None:
        self.marker.write_bytes(TAG.encode() + b"\0")
        self.assert_unavailable(self.run_launcher("hook"))

    def test_oversized_marker_is_rejected_before_interpreter_execution(self) -> None:
        self.marker.write_bytes(b"x" * 100_000)
        self.assert_unavailable(self.run_launcher("hook"))

    def test_marker_without_final_newline_is_accepted(self) -> None:
        self.marker.write_text(TAG)
        self.assertEqual(self.run_launcher("hook").returncode, 0)
        self.assertTrue((self.root / "arguments.txt").exists())

    def test_symlink_marker_is_rejected(self) -> None:
        real = self.runtime / "real-marker"
        self.marker.rename(real)
        self.marker.symlink_to(real)
        self.assert_unavailable(self.run_launcher("hook"))

    def test_directory_marker_is_rejected(self) -> None:
        self.marker.unlink()
        self.marker.mkdir()
        self.assert_unavailable(self.run_launcher("hook"))

    def test_nonexecutable_interpreter_is_rejected(self) -> None:
        self.python.chmod(0o600)
        self.assert_unavailable(self.run_launcher("hook"))

    def test_missing_interpreter_has_no_system_fallback(self) -> None:
        self.python.unlink()
        self.assert_unavailable(self.run_launcher("hook"))

    def test_relative_runtime_override_is_rejected(self) -> None:
        self.env["GUARDTRELLIS_CURSOR_RUNTIME"] = "external runtime"
        self.assert_unavailable(self.run_launcher("hook"))

    def test_empty_runtime_override_is_rejected(self) -> None:
        self.env["GUARDTRELLIS_CURSOR_RUNTIME"] = ""
        self.assert_unavailable(self.run_launcher("hook"))

    def test_missing_runtime_is_rejected(self) -> None:
        self.env["GUARDTRELLIS_CURSOR_RUNTIME"] = str(self.root / "not installed")
        self.assert_unavailable(self.run_launcher("hook"))

    def test_runtime_inside_plugin_is_rejected(self) -> None:
        inner = self.plugin / "forbidden-runtime"
        shutil.copytree(self.runtime, inner)
        self.env["GUARDTRELLIS_CURSOR_RUNTIME"] = str(inner)
        self.assert_unavailable(self.run_launcher("hook"))

    def test_symlink_runtime_into_plugin_is_rejected(self) -> None:
        inner = self.plugin / "forbidden-runtime"
        shutil.copytree(self.runtime, inner)
        alias = self.root / "runtime alias"
        alias.symlink_to(inner, target_is_directory=True)
        self.env["GUARDTRELLIS_CURSOR_RUNTIME"] = str(alias)
        self.assert_unavailable(self.run_launcher("hook"))

    def test_missing_adapter_is_rejected_before_execution(self) -> None:
        (self.plugin / "adapters/cursor/prompt_check.py").unlink()
        self.assert_unavailable(self.run_launcher("hook"))

    def test_symlink_adapter_is_rejected_before_execution(self) -> None:
        target = self.plugin / "adapters/cursor/prompt_check.py"
        other = self.root / "other.py"
        target.rename(other)
        target.symlink_to(other)
        self.assert_unavailable(self.run_launcher("hook"))

    def test_missing_prepare_adapter_never_opens_or_emits_raw_text(self) -> None:
        (self.plugin / "adapters/cursor/prepare_prompt.py").unlink()
        self.assert_unavailable(self.run_launcher("prepare", "--open"), prepare=True)

    def test_unknown_profile_cannot_silently_weaken_enforcement(self) -> None:
        self.assert_unavailable(
            self.run_launcher("hook", "--profile", "other"),
            blocked=True,
            reason="invalid_configuration",
        )

    def test_extra_hook_arguments_are_rejected_without_echo(self) -> None:
        self.assert_unavailable(
            self.run_launcher("hook", "--profile", "advisory", "do-not-echo"),
            blocked=True,
            reason="invalid_configuration",
        )

    def test_prepare_rejects_unknown_options_without_echo(self) -> None:
        self.assert_unavailable(
            self.run_launcher("prepare", "--send", "do-not-echo"),
            prepare=True,
            reason="invalid_configuration",
        )

    def test_unknown_mode_is_an_error_without_prompt_output(self) -> None:
        self.assert_unavailable(
            self.run_launcher("unknown"), prepare=True, reason="invalid_configuration"
        )

    def test_missing_mode_is_an_error(self) -> None:
        self.assert_unavailable(self.run_launcher(), prepare=True, reason="invalid_configuration")

    def test_child_status_is_preserved_without_retry_or_fallback(self) -> None:
        self.env["GT_CURSOR_TEST_EXIT"] = "7"
        result = self.run_launcher("hook")
        self.assertEqual(result.returncode, 7)
        self.assertTrue((self.root / "arguments.txt").exists())


if __name__ == "__main__":
    unittest.main()
