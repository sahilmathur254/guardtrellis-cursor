"""Prepare a reviewed local draft; an explicit --open requests Cursor prefill only."""

from __future__ import annotations

import json
import subprocess
import sys
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex import redact_prompt as redactor  # noqa: E402
from common import prompt_runtime as runtime  # noqa: E402

MAX_INPUT_BYTES = redactor.MAX_INPUT_BYTES
MAX_URI_CHARS = 10_000
LAUNCH_TIMEOUT_SECONDS = 5
URI_PREFIX = "cursor://anysphere.cursor-deeplink/prompt?text="
FINDING_CODES = frozenset(
    (
        "secret_github_classic",
        "secret_github_fine_grained",
        "secret_aws_access_key_id",
        "secret_private_key",
        "pii_email",
        "pii_phone",
        "finding_limit_exceeded",
        "scanner_error",
    )
)
REASONS = frozenset(
    (
        "clean_prompt",
        "pii_redacted",
        "secret_detected",
        "input_too_large",
        "invalid_utf8",
        "prompt_too_large",
        "runtime_unavailable",
        "sdk_version_mismatch",
        "scan_failed",
    )
)


@dataclass(frozen=True)
class Prepared:
    text: str | None = field(repr=False)
    report: dict[str, object]
    exit_code: int


def _report(reason: str, *, status: str = "unavailable") -> dict[str, object]:
    return {
        "contract": "cursor_reviewed_prefill_v1",
        "boundary": "local_reviewed_prefill",
        "check_status": status,
        "scanner_action": None,
        "reason_code": reason,
        "finding_codes": [],
        "pii_formats": list(runtime.PII_FORMATS),
        "sdk_version": None,
        "prefill_status": "not_requested",
        "submission": "not_performed",
    }


def _launch(uri: str) -> bool:
    completed = subprocess.run(
        ["/usr/bin/open", "-a", "/Applications/Cursor.app", uri],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=LAUNCH_TIMEOUT_SECONDS,
    )
    return completed.returncode == 0


def prepare_prompt(
    raw: bytes,
    *,
    open_cursor: bool = False,
    platform: str | None = None,
    launcher: Callable[[str], bool] | None = None,
) -> Prepared:
    """Withhold secrets/errors; open mode passes only accepted text to the launcher."""
    report = _report("scan_failed")
    try:
        preview = redactor.redact_prompt(raw)
        source = preview.report
        status = source.get("check_status")
        reason = source.get("reason_code")
        action = source.get("scanner_action")
        codes = source.get("finding_codes")
        version = source.get("sdk_version")
        # Copy only fixed metadata vocabulary, never arbitrary upstream report fields.
        if (
            type(status) is not str
            or status not in ("checked", "invalid_input", "unavailable")
            or type(reason) is not str
            or reason not in REASONS
            or (action is not None and action not in ("allow", "redact", "block", "error"))
            or type(codes) is not list
            or len(codes) > len(FINDING_CODES)
            or any(type(code) is not str or code not in FINDING_CODES for code in codes)
            or (version is not None and version != runtime.EXPECTED_SDK_VERSION)
        ):
            raise ValueError
        report = _report(reason, status=status)
        report.update(scanner_action=action, finding_codes=sorted(set(codes)), sdk_version=version)
        text = preview.text
        if text is None:
            return Prepared(None, report, 1)
        if (
            type(text) is not str
            or preview.exit_code != 0
            or status != "checked"
            or action not in ("allow", "redact")
            or version != runtime.EXPECTED_SDK_VERSION
            or reason not in ("clean_prompt", "pii_redacted")
        ):
            raise ValueError
        text.encode("utf-8")
    except Exception:
        return Prepared(None, _report("scan_failed"), 1)
    if not open_cursor:
        return Prepared(text, report, 0)
    report["prefill_status"] = "unavailable"
    if (sys.platform if platform is None else platform) != "darwin":
        report["reason_code"] = "unsupported_platform"
        return Prepared(None, report, 1)
    if not text.strip():
        report["reason_code"] = "empty_draft"
        return Prepared(None, report, 1)
    if any(
        character not in "\r\n\t" and unicodedata.category(character)[0] not in "LMNPSZ"
        for character in text
    ):
        report["reason_code"] = "unsupported_draft_characters"
        return Prepared(None, report, 1)
    uri = URI_PREFIX + quote(text, safe="", encoding="utf-8", errors="strict")
    if len(uri) > MAX_URI_CHARS:
        report["reason_code"] = "uri_too_large"
        return Prepared(None, report, 1)
    try:
        if (launcher or _launch)(uri) is not True:
            raise OSError
    except Exception:
        report["reason_code"] = "launch_failed"
        return Prepared(None, report, 1)
    report.update(reason_code="prefill_requested", prefill_status="requested")
    return Prepared(None, report, 0)


def _emit(prepared: Prepared) -> int:
    if sys.stdout is None or sys.stderr is None:
        return 1
    try:
        serialized = json.dumps(prepared.report, ensure_ascii=True, allow_nan=False) + "\n"
        if sys.stderr.write(serialized) != len(serialized):
            raise OSError
        sys.stderr.flush()
    except Exception:
        try:
            runtime._discard_failed_stream(sys.stderr)
        except Exception:
            pass
        return 1
    if prepared.text is not None:
        try:
            encoded = prepared.text.encode("utf-8")
            if sys.stdout.buffer.write(encoded) != len(encoded):
                raise OSError
            sys.stdout.buffer.flush()
        except Exception:
            try:
                runtime._discard_failed_stream(sys.stdout)
            except Exception:
                pass
            return 1
    return prepared.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    options = list(sys.argv[1:] if argv is None else argv)
    if options not in ([], ["--open"]):
        return _emit(Prepared(None, _report("invalid_configuration"), 1))
    # Check diagnostic availability before requesting an external application action.
    if sys.stderr is None or sys.stdout is None:
        return 1
    try:
        if sys.stderr.write("") != 0:
            raise OSError
        sys.stderr.flush()
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if not isinstance(raw, bytes):
            raise OSError
    except Exception:
        return _emit(Prepared(None, _report("stream_unavailable"), 1))
    return _emit(prepare_prompt(raw, open_cursor=options == ["--open"]))


if __name__ == "__main__":
    raise SystemExit(main())
