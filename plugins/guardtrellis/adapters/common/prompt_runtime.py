"""Shared bounded prompt checks and JSON transport; host activation is external."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from importlib import metadata
from typing import TYPE_CHECKING, NoReturn, TextIO

if TYPE_CHECKING:
    from guardtrellis import Result

EXPECTED_SDK_VERSION = "0.1.9"
MAX_EVENT_BYTES = 65_536
MAX_PROMPT_CHARS = 10_000
PII_FORMATS = ("email", "phone")


@dataclass(frozen=True)
class Outcome:
    """Only static metadata and host decisions; no event or prompt is retained here."""

    response: dict[str, object]
    report: dict[str, object]
    exit_code: int = 0


def _outcome(
    status: str,
    action: str,
    reason: str,
    *,
    profile: str = "prompt_v1",
    scanner_action: str | None = None,
    finding_codes: Sequence[str] = (),
    sdk_version: str | None = None,
    exit_code: int = 0,
    pii_policy: str = "off",
) -> Outcome:
    response: dict[str, object] = {}
    if action == "block":
        if reason == "secret_detected":
            message = "GuardTrellis: recognized secret signature in submitted prompt."
        elif reason in ("pii_detected", "secret_and_pii_detected"):
            message = (
                "GuardTrellis: detected email or international phone number; blocking requested. "
                "Run the local redaction preview, review its output, and resubmit. "
                "Remove any recognized secret signatures too."
            )
        else:
            message = (
                "GuardTrellis: prompt check failed; configured error policy requests blocking."
            )
        response = {"decision": "block", "reason": message}
    elif action == "warn":
        if reason == "secret_detected":
            message = (
                "GuardTrellis advisory: recognized secret signature detected; prompt unchanged."
            )
        elif reason in ("pii_detected", "secret_and_pii_detected"):
            message = (
                "GuardTrellis advisory: detected email or international phone number; "
                "prompt unchanged; advisory only. Use the local redaction preview "
                "before future submissions; remove any recognized secret signatures too."
            )
        elif status == "unsupported":
            message = "GuardTrellis: unsupported hook event; prompt check not performed."
        else:
            message = "GuardTrellis: prompt check did not complete; review adapter diagnostics."
        response = {"systemMessage": message}
    report: dict[str, object] = {
        "profile": profile,
        "boundary": "user_prompt_submit.prompt",
        "check_status": status,
        "policy_action": action,
        "scanner_action": scanner_action,
        "reason_code": reason,
        "finding_codes": sorted(set(finding_codes)),
        "sdk_version": sdk_version,
        "host_enforcement": "not_observed",
    }
    if pii_policy != "off":
        report.update(pii_policy=pii_policy, pii_formats=list(PII_FORMATS))
    return Outcome(response=response, report=report, exit_code=exit_code)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise ValueError("nonfinite_json")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("nonfinite_json")
    return parsed


def decode_event(raw: bytes) -> object:
    """Decode one bounded UTF-8 JSON value without relaxing host-specific policy."""
    if len(raw) > MAX_EVENT_BYTES:
        raise ValueError("event_too_large")
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
        parse_float=_finite_float,
    )


def scan_prompt(prompt: str, block_secrets: bool, pii: str = "off") -> Result:
    # Lazy import allows the executable to report a missing SDK without a traceback.
    from guardtrellis import Action, Guard, PIIScanner, SecretScanner, Stage

    guard = Guard(
        input_scanners=[
            SecretScanner(action=Action.BLOCK if block_secrets else Action.WARN),
            *(
                [
                    PIIScanner(
                        formats=PII_FORMATS, action=Action.BLOCK if pii == "block" else Action.WARN
                    )
                ]
                if pii != "off"
                else []
            ),
        ],
        max_chars=MAX_PROMPT_CHARS,
    )
    return guard.scan(prompt, stage=Stage.INPUT)


def handle_event(
    raw: bytes,
    *,
    block_secrets: bool = False,
    on_error: str = "warn",
    pii: str = "off",
    profile: str,
    scanner: Callable[[str, bool, str], Result] = scan_prompt,
) -> Outcome:
    """Inspect one bounded event and return a host response plus separate diagnostics.

    Error blocking applies only after recognizing UserPromptSubmit. Unparseable or
    unsupported envelopes cannot establish that event and always produce a warning.
    """
    outcome = partial(_outcome, profile=profile)
    if (
        type(block_secrets) is not bool
        or on_error not in ("warn", "block")
        or pii not in ("off", "warn", "block")
    ):
        return outcome("unavailable", "warn", "invalid_configuration", exit_code=1)
    outcome = partial(_outcome, profile=profile, pii_policy=pii)
    if len(raw) > MAX_EVENT_BYTES:
        return outcome("invalid_event", "warn", "event_too_large")
    try:
        event = decode_event(raw)
    except (ValueError, UnicodeError, RecursionError):
        return outcome("invalid_event", "warn", "invalid_json")
    if not isinstance(event, dict):
        return outcome("invalid_event", "warn", "invalid_event")
    event_name = event.get("hook_event_name")
    if not isinstance(event_name, str) or not event_name:
        return outcome("invalid_event", "warn", "invalid_event")
    if event_name != "UserPromptSubmit":
        return outcome("unsupported", "warn", "unsupported_event")

    # All other fields, including file paths and session identifiers, are ignored.
    prompt = event.get("prompt")
    if not isinstance(prompt, str):
        return outcome("invalid_event", on_error, "invalid_event")
    if len(prompt) > MAX_PROMPT_CHARS:
        return outcome("unavailable", on_error, "prompt_too_large")
    try:
        prompt.encode("utf-8")
    except UnicodeError:
        return outcome("invalid_event", on_error, "invalid_event")

    try:
        installed_version = metadata.version("guardtrellis")
    except Exception:
        return outcome("unavailable", on_error, "runtime_unavailable")
    if installed_version != EXPECTED_SDK_VERSION:
        # Do not echo arbitrary distribution metadata on the protocol streams.
        return outcome("unavailable", on_error, "sdk_version_mismatch")
    try:
        result = scanner(prompt, block_secrets, pii)
    except ImportError:
        return outcome(
            "unavailable",
            on_error,
            "runtime_unavailable",
            sdk_version=EXPECTED_SDK_VERSION,
        )
    except Exception:
        return outcome("unavailable", on_error, "scan_failed", sdk_version=EXPECTED_SDK_VERSION)

    # These codes originate in the pinned SDK's built-in scanner, never event fields.
    codes = [finding.code for finding in result.findings]
    action = result.action.value
    if action == "error":
        return outcome(
            "unavailable",
            on_error,
            "scan_failed",
            scanner_action=action,
            finding_codes=codes,
            sdk_version=EXPECTED_SDK_VERSION,
        )
    has_pii = any(code.startswith("pii_") for code in codes)
    has_secret = any(code.startswith("secret_") for code in codes)
    reason = "clean_prompt"
    if has_pii and has_secret:
        reason = "secret_and_pii_detected"
    elif has_pii:
        reason = "pii_detected"
    elif has_secret:
        reason = "secret_detected"
    return outcome(
        "checked",
        action,
        reason,
        scanner_action=action,
        finding_codes=codes,
        sdk_version=EXPECTED_SDK_VERSION,
    )


class _InvalidConfiguration(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        # argparse's default error includes user-supplied argument values.
        raise _InvalidConfiguration


def _discard_failed_stream(stream: TextIO) -> None:
    """Prevent Python's shutdown flush from retrying a broken protocol pipe."""
    try:
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), stream.fileno())
    except (OSError, ValueError):
        try:
            stream.close()
        except (OSError, ValueError):
            pass


def _emit(outcome: Outcome) -> int:
    # Python uses None for a standard stream whose descriptor was absent at startup.
    if sys.stdout is None or sys.stderr is None:
        return 1
    for stream, payload in (
        (sys.stdout, outcome.response),
        (sys.stderr, outcome.report),
    ):
        try:
            print(json.dumps(payload), file=stream, flush=True)
        except (OSError, ValueError):
            _discard_failed_stream(stream)
            # A complete response/report pair cannot be assumed after this failure.
            return 1
    return outcome.exit_code


def main(
    argv: Sequence[str] | None = None,
    *,
    host: str,
    handler: Callable[..., Outcome],
) -> int:
    outcome = partial(_outcome, profile=f"{host}_prompt_v1")
    parser = _Parser(
        prog=f"guardtrellis-{host}-prompt",
        description=f"Inspect one {host} UserPromptSubmit event; no hooks are installed.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--block-secrets",
        action="store_true",
        help="Request blocking for the pinned SDK's whole recognized secret-signature family.",
    )
    parser.add_argument(
        "--on-error",
        choices=("warn", "block"),
        default="warn",
        help="Response on a failed check for a recognized UserPromptSubmit event (default: warn).",
    )
    if host == "codex":
        parser.add_argument(
            "--pii",
            choices=("off", "warn", "block"),
            default="off",
            help="Email and international phone detection policy (default: off); never rewrites.",
        )
    try:
        options = parser.parse_args(argv)
    except _InvalidConfiguration:
        return _emit(outcome("unavailable", "warn", "invalid_configuration", exit_code=1))
    try:
        # Read at most one byte beyond the bound; do not consume arbitrary input.
        raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
        if raw is None:  # A nonblocking pipe can have no bytes available yet.
            raise BlockingIOError
    except (AttributeError, OSError, ValueError):
        return _emit(outcome("unavailable", "warn", "stdin_unavailable", exit_code=1))
    pii_options = {"pii": options.pii} if host == "codex" else {}
    return _emit(
        handler(raw, block_secrets=options.block_secrets, on_error=options.on_error, **pii_options)
    )
