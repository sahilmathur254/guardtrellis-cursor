"""Offline prefill routing regressions; no real CLI, editor or provider is invoked."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "native_prefill", ROOT / "plugins/guardtrellis/adapters/cursor/prepare_prompt.py"
)
assert SPEC is not None and SPEC.loader is not None
preparer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preparer
SPEC.loader.exec_module(preparer)

EMAIL = "mira@example.org"
PHONE = "+14155550123"
SECRET = "ghp_" + "a" * 36


class Output:
    def __init__(self) -> None:
        self.text = io.StringIO()
        self.buffer = io.BytesIO()

    def write(self, value: str) -> int:
        return self.text.write(value)

    def flush(self) -> None:
        self.text.flush()


class PrefillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gt-prefill-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.data = self.root / "owned data with spaces"
        self.extensions = self.root / "owned extensions with spaces"
        self.data.mkdir()
        self.extensions.mkdir()
        self.profile = "GT Review Test"
        self.target = preparer.launch_target(str(self.data), str(self.extensions), self.profile)
        self.args = [
            "--open",
            "--user-data-dir",
            str(self.data),
            "--extensions-dir",
            str(self.extensions),
            "--cursor-profile",
            self.profile,
        ]
        self.raw = f"Mira {EMAIL} {PHONE}".encode()
        self.masked = "Mira [PII] [PII]"
        self.scan = self.enterContext(
            patch.object(preparer.redactor, "redact_prompt", side_effect=self.preview)
        )
        self.child = self.enterContext(
            patch.object(preparer.subprocess, "run", return_value=SimpleNamespace(returncode=0))
        )

    def preview(self, raw: bytes):
        return preparer.redactor.Preview(
            text=self.masked,
            report={
                "check_status": "checked",
                "reason_code": "pii_redacted",
                "scanner_action": "redact",
                "finding_codes": ["pii_email", "pii_phone"],
                "sdk_version": "0.1.9",
            },
            exit_code=0,
        )

    def main(self, options):
        output, errors = Output(), Output()
        with (
            patch.object(preparer.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(self.raw))),
            patch.object(preparer.sys, "stdout", output),
            patch.object(preparer.sys, "stderr", errors),
            patch.object(preparer.sys, "platform", "darwin"),
        ):
            code = preparer.main(options)
        return code, output.buffer.getvalue(), errors.text.getvalue()

    def test_preview_without_target_is_unchanged_and_never_launches(self):
        code, text, errors = self.main([])
        self.assertEqual((code, text), (0, self.masked.encode()))
        self.assertEqual(json.loads(errors)["prefill_status"], "not_requested")
        self.child.assert_not_called()

    def test_complete_target_dispatches_exact_masked_argv_without_os_opener(self):
        code, text, errors = self.main(self.args)
        self.assertEqual((code, text), (0, b""))
        self.assertEqual(json.loads(errors)["submission"], "not_performed")
        self.assertEqual(json.loads(errors)["prefill_status"], "requested")
        argv = self.child.call_args.args[0]
        self.assertEqual(
            argv[:-1],
            [
                preparer.CURSOR_CLI,
                "--user-data-dir",
                str(self.data),
                "--extensions-dir",
                str(self.extensions),
                "--profile",
                self.profile,
                "--open-url",
            ],
        )
        self.assertEqual(parse_qs(urlsplit(argv[-1]).query), {"text": [self.masked]})
        self.assertNotIn(EMAIL, repr((argv, errors)))
        self.assertNotIn(PHONE, repr((argv, errors)))
        self.assertEqual(self.child.call_count, 1)

    def test_environment_drops_remote_portable_node_and_shell_routing(self):
        poisoned = dict.fromkeys(
            [
                "VSCODE_IPC_HOOK_CLI",
                "VSCODE_CWD",
                "VSCODE_PORTABLE",
                "VSCODE_DEV",
                "NODE_OPTIONS",
                "NODE_REPL_EXTERNAL_MODULE",
                "ELECTRON_RUN_AS_NODE",
                "CURSOR_CLI",
                "CURSOR_CLI_MODE",
                "CURSOR_DESKTOP_BRIDGE_DIR",
                "BASH_ENV",
                "ENV",
            ],
            "private-environment-canary",
        )
        poisoned.update(
            HOME=str(Path.home()),
            PATH="/private/bad",
            LANG="en_US.UTF-8",
            GUARDTRELLIS_CURSOR_RUNTIME="/synthetic/owned-runtime",
        )
        with patch.dict(os.environ, poisoned, clear=True):
            preparer._launch(preparer.URI_PREFIX + "masked", self.target)
        kw = self.child.call_args.kwargs
        self.assertEqual(
            kw["env"],
            {
                "HOME": str(Path.home()),
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "LANG": "en_US.UTF-8",
                "GUARDTRELLIS_CURSOR_RUNTIME": "/synthetic/owned-runtime",
            },
        )
        self.assertNotIn("shell", kw)
        self.assertEqual(kw["cwd"], str(self.data))
        self.assertEqual(kw["timeout"], 5)
        for key in ("stdin", "stdout", "stderr"):
            self.assertEqual(kw[key], subprocess.DEVNULL)

    def test_incomplete_unknown_duplicate_and_value_injection_options_fail_before_input(self):
        invalid = [
            ["--open"],
            self.args[:-1],
            self.args + ["--open"],
            ["--help"],
            [EMAIL],
            ["--open=true"],
            ["--open", "--user-data-dir", str(self.data)] * 2,
            self.args[:3] + ["--user-data-dir"] + self.args[4:],
            self.args[:3] + ["--unknown-private-option"] + self.args[4:],
            ["--cursor-profile", self.profile],
        ]
        for args in invalid:
            with self.subTest(args=args):
                code, text, errors = self.main(args)
                self.assertEqual((code, text), (1, b""))
                self.assertEqual(json.loads(errors)["reason_code"], "invalid_configuration")
                self.assertNotIn(EMAIL, errors)
                self.assertNotIn(str(self.root), errors)
        self.child.assert_not_called()
        self.scan.assert_not_called()

    def test_python_options_allow_complete_pairs_in_any_order(self):
        options = [
            "--open",
            "--cursor-profile",
            self.profile,
            "--extensions-dir",
            str(self.extensions),
            "--user-data-dir",
            str(self.data),
        ]
        self.assertEqual(preparer._options(options), (True, self.target))

    def test_directory_targets_refuse_relative_missing_overlap_linked_and_normal_storage(self):
        linked = self.root / "linked"
        linked.symlink_to(self.data, target_is_directory=True)
        child = self.data / "nested"
        child.mkdir()
        for first, second in [
            ("relative", str(self.extensions)),
            (str(self.root / "missing"), str(self.extensions)),
            (str(self.data), str(self.data)),
            (str(self.data), str(child)),
            (str(linked), str(self.extensions)),
            (str(Path.home()), str(self.extensions)),
            (str(Path.home() / ".cursor"), str(self.extensions)),
            ("/Applications/Cursor.app", str(self.extensions)),
            (str(self.data) + "\n", str(self.extensions)),
        ]:
            with self.subTest(first=first, second=second):
                with self.assertRaises((ValueError, OSError)):
                    preparer.launch_target(first, second, self.profile)
        self.child.assert_not_called()

    def test_identity_aliases_cannot_bypass_protected_or_overlap_checks(self):
        # Mock identity to cover case-insensitive filesystems without touching
        # the real normal profile or skipping this regression on other volumes.
        first, other = self.data, self.extensions
        original = Path.samefile

        def samefile(path, compared):
            if path == other and compared == first:
                return True
            return original(path, compared)

        with patch.object(Path, "samefile", samefile):
            self.assertTrue(preparer._overlaps(first, other))
            with self.assertRaises(ValueError):
                preparer.launch_target(str(first), str(other), self.profile)
        protected = Path.home() / ".cursor"

        def protected_identity(path, compared):
            if path == first and compared == protected:
                return True
            return original(path, compared)

        with patch.object(Path, "samefile", protected_identity):
            with self.assertRaises(ValueError):
                preparer.launch_target(str(first), str(other), self.profile)
        self.child.assert_not_called()

    def test_absent_protected_leaf_still_checks_existing_identity_ancestors(self):
        original = Path.samefile
        alias = self.extensions
        absent_leaf = self.data / "absent-protected-root"

        def samefile(path, compared):
            if path == self.data and compared == alias:
                return True
            return original(path, compared)

        with patch.object(Path, "samefile", samefile):
            self.assertTrue(preparer._overlaps(alias, absent_leaf))
        self.child.assert_not_called()

    def test_profile_rejects_control_options_paths_and_unbounded_names(self):
        for profile in ["", "--send", "../normal", "bad\nname", " name", "name ", "x" * 81]:
            with self.subTest(profile=profile):
                with self.assertRaises(ValueError):
                    preparer.launch_target(str(self.data), str(self.extensions), profile)
        self.child.assert_not_called()

    def test_target_is_revalidated_before_dispatch(self):
        self.extensions.rmdir()
        result = preparer.prepare_prompt(
            self.raw, open_cursor=True, platform="darwin", target=self.target
        )
        self.assertEqual(result.report["reason_code"], "launch_failed")
        self.assertIsNone(result.text)
        self.child.assert_not_called()

    def test_child_nonzero_missing_and_timeout_have_no_payload_retry_or_fallback(self):
        for failure in [
            False,
            OSError(f"private-child-canary {EMAIL}"),
            subprocess.TimeoutExpired(EMAIL, 5, output=PHONE, stderr=SECRET),
        ]:
            with self.subTest(failure=type(failure).__name__):
                self.child.reset_mock()
                self.child.side_effect = failure if isinstance(failure, Exception) else None
                self.child.return_value = SimpleNamespace(returncode=1)
                result = preparer.prepare_prompt(
                    self.raw, open_cursor=True, platform="darwin", target=self.target
                )
                self.assertEqual(result.exit_code, 1)
                self.assertIsNone(result.text)
                self.assertEqual(result.report["reason_code"], "launch_failed")
                self.assertEqual(self.child.call_count, 1)
                for canary in [EMAIL, PHONE, SECRET, "private-child-canary", str(self.root)]:
                    self.assertNotIn(canary, repr(result))

    def test_rejected_secrets_and_scan_failures_never_dispatch(self):
        for reason in ["secret_detected", "runtime_unavailable", "scan_failed"]:
            with self.subTest(reason=reason):
                self.scan.side_effect = None
                self.scan.return_value = preparer.redactor.Preview(
                    text=None,
                    report={
                        "check_status": "unavailable",
                        "reason_code": reason,
                        "scanner_action": "error",
                        "finding_codes": [],
                        "sdk_version": None,
                    },
                    exit_code=1,
                )
                result = preparer.prepare_prompt(
                    SECRET.encode(), open_cursor=True, platform="darwin", target=self.target
                )
                self.assertEqual(result.exit_code, 1)
                self.assertIsNone(result.text)
                self.assertNotIn(SECRET, repr(result))
        self.child.assert_not_called()

    def test_programmatic_open_requires_target_or_explicit_callback(self):
        result = preparer.prepare_prompt(self.raw, open_cursor=True, platform="darwin")
        self.assertEqual(result.report["reason_code"], "invalid_configuration")
        self.child.assert_not_called()

    def test_platform_control_and_encoded_url_limits_withhold_launch(self):
        for text, platform, reason in [
            ("Clean", "linux", "unsupported_platform"),
            ("  \n", "darwin", "empty_draft"),
            ("bad\x1b", "darwin", "unsupported_draft_characters"),
            ("🌳" * 1000, "darwin", "uri_too_large"),
        ]:
            with self.subTest(reason=reason):
                self.masked = text
                result = preparer.prepare_prompt(
                    self.raw, open_cursor=True, platform=platform, target=self.target
                )
                self.assertEqual(result.report["reason_code"], reason)
                self.assertIsNone(result.text)
        self.child.assert_not_called()

    def test_launch_target_repr_omits_local_paths_and_profile(self):
        for value in [str(self.root), self.profile]:
            self.assertNotIn(value, repr(self.target))


if __name__ == "__main__":
    unittest.main()
