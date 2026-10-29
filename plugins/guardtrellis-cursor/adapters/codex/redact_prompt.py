"""Local plaintext preview: block known secret shapes, redact configured PII shapes.

Review the output before submitting it. Names, obfuscated forms, and other PII can
remain; this command does not submit text to a host or model.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import prompt_runtime as runtime  # noqa: E402

MAX_PROMPT_CHARS = runtime.MAX_PROMPT_CHARS
MAX_INPUT_BYTES = 4 * MAX_PROMPT_CHARS


@dataclass(frozen=True)
class Preview:
    text: str | None = field(repr=False)
    report: dict[str, object]
    exit_code: int


def _preview(
    status: str,
    reason: str,
    *,
    text: str | None = None,
    action: str | None = None,
    codes: Sequence[str] = (),
    sdk_version: str | None = None,
) -> Preview:
    return Preview(
        text=text,
        report={
            "profile": "codex_local_redaction_v1",
            "boundary": "local_stdout_preview",
            "check_status": status,
            "scanner_action": action,
            "reason_code": reason,
            "finding_codes": sorted(set(codes)),
            "pii_formats": list(runtime.PII_FORMATS),
            "sdk_version": sdk_version,
            "submission": "not_performed",
        },
        exit_code=0 if text is not None else 1,
    )


def redact_prompt(raw: bytes) -> Preview:
    """Return checked text only after the pinned, fixed input policy accepts it."""
    if len(raw) > MAX_INPUT_BYTES:
        return _preview("invalid_input", "input_too_large")
    try:
        prompt = raw.decode("utf-8")
    except UnicodeError:
        return _preview("invalid_input", "invalid_utf8")
    if len(prompt) > MAX_PROMPT_CHARS:
        return _preview("invalid_input", "prompt_too_large")
    try:
        installed_version = metadata.version("guardtrellis")
    except Exception:
        return _preview("unavailable", "runtime_unavailable")
    if installed_version != runtime.EXPECTED_SDK_VERSION:
        return _preview("unavailable", "sdk_version_mismatch")
    try:
        from guardtrellis import Action, Guard, PIIScanner, SecretScanner, Stage

        result = Guard(
            input_scanners=[
                SecretScanner(action=Action.BLOCK),
                PIIScanner(formats=runtime.PII_FORMATS, action=Action.REDACT),
            ],
            max_chars=MAX_PROMPT_CHARS,
        ).scan(prompt, stage=Stage.INPUT)
        codes = [finding.code for finding in result.findings]
        action = result.action.value
        if result.action == Action.BLOCK:
            return _preview(
                "checked",
                "secret_detected",
                action=action,
                codes=codes,
                sdk_version=runtime.EXPECTED_SDK_VERSION,
            )
        if result.action == Action.ERROR:
            return _preview(
                "unavailable",
                "scan_failed",
                action=action,
                codes=codes,
                sdk_version=runtime.EXPECTED_SDK_VERSION,
            )
        return _preview(
            "checked",
            "pii_redacted" if result.action == Action.REDACT else "clean_prompt",
            text=result.require_text(),
            action=action,
            codes=codes,
            sdk_version=runtime.EXPECTED_SDK_VERSION,
        )
    except ImportError:
        return _preview(
            "unavailable", "runtime_unavailable", sdk_version=runtime.EXPECTED_SDK_VERSION
        )
    except Exception:
        return _preview("unavailable", "scan_failed", sdk_version=runtime.EXPECTED_SDK_VERSION)


def _emit(preview: Preview) -> int:
    if sys.stdout is None or sys.stderr is None:
        return 1
    # Confirm the diagnostic stream works before releasing any checked text.
    try:
        print(json.dumps(preview.report), file=sys.stderr, flush=True)
    except (OSError, ValueError):
        runtime._discard_failed_stream(sys.stderr)
        return 1
    if preview.text is not None:
        try:
            sys.stdout.buffer.write(preview.text.encode("utf-8"))
            sys.stdout.buffer.flush()
        except (AttributeError, OSError, ValueError):
            runtime._discard_failed_stream(sys.stdout)
            return 1
    return preview.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = runtime._Parser(
        prog="guardtrellis-redact-prompt",
        description=(
            "Read bounded UTF-8 plaintext from stdin and print a local review preview. "
            "Blocks recognized secret signatures; redacts ASCII email and contiguous "
            "international phone shapes. Names and obfuscated forms may remain. "
            "No prompt is submitted."
        ),
        allow_abbrev=False,
    )
    try:
        parser.parse_args(argv)
    except runtime._InvalidConfiguration:
        return _emit(_preview("unavailable", "invalid_configuration"))
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if raw is None:  # A nonblocking pipe can have no bytes available yet.
            raise BlockingIOError
    except (AttributeError, OSError, ValueError):
        return _emit(_preview("unavailable", "stdin_unavailable"))
    return _emit(redact_prompt(raw))


if __name__ == "__main__":
    raise SystemExit(main())
