"""Offline Cursor beforeSubmitPrompt adapter; no hooks are installed or activated."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Sequence
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

# Isolated Python still resolves this bundled module from its own installed path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import prompt_runtime as runtime  # noqa: E402

if TYPE_CHECKING:
    from guardtrellis import Result

Outcome = runtime.Outcome
EXPECTED_SDK_VERSION = runtime.EXPECTED_SDK_VERSION
MAX_EVENT_BYTES = runtime.MAX_EVENT_BYTES
MAX_PROMPT_CHARS = runtime.MAX_PROMPT_CHARS
MAX_RESPONSE_BYTES = 4_096
MAX_REPORT_BYTES = 2_048
CONTRACT = "cursor_prompt_v1"
PROFILES = ("advisory", "enforce-secrets-v1")
DIAGNOSTICS = ("all", "findings")
SECRET_CODES = frozenset(
    (
        "secret_github_classic",
        "secret_github_fine_grained",
        "secret_aws_access_key_id",
        "secret_private_key",
    )
)
SECRET_MESSAGE = "GuardTrellis detected a recognized secret pattern. Remove it and resubmit."
UNAVAILABLE_MESSAGE = (
    "GuardTrellis could not check this prompt. This configured check requests cancellation."
)
_scan_prompt = runtime.scan_prompt


def _outcome(
    status: str,
    reason: str,
    *,
    profile: str | None,
    scanner_action: str | None = None,
    finding_codes: Sequence[str] = (),
    sdk_version: str | None = None,
) -> Outcome:
    checked = status == "checked"
    blocked = profile != "advisory" and not (checked and scanner_action == "allow")
    action = "block" if blocked else "allow" if checked and scanner_action == "allow" else "warn"
    response: dict[str, object] = {"continue": not blocked}
    if blocked:
        response["user_message"] = SECRET_MESSAGE if checked else UNAVAILABLE_MESSAGE
    return Outcome(
        response=response,
        report={
            "contract": CONTRACT,
            "profile": profile,
            "boundary": "beforeSubmitPrompt.prompt",
            "check_status": status,
            "policy_action": action,
            "scanner_action": scanner_action,
            "reason_code": reason,
            "finding_codes": sorted(set(finding_codes)),
            "sdk_version": sdk_version,
            "requested_continue": not blocked,
            "host_enforcement": "not_observed",
        },
    )


def _assess_result(result: object, prompt: str, block_secrets: bool) -> tuple[str, list[str]]:
    """Accept only the pinned SDK's unchanged single-SecretScanner result contract."""
    from guardtrellis import Action, Finding, Result, Stage

    if (
        not isinstance(result, Result)
        or not isinstance(result.action, Action)
        or result.stage is not Stage.INPUT
    ):
        raise ValueError
    if result.action is Action.ERROR:
        return "error", []
    expected = Action.BLOCK if block_secrets else Action.WARN
    if result.action not in (Action.ALLOW, expected):
        raise ValueError
    if type(result.findings) is not tuple or len(result.findings) > 256:
        raise ValueError
    if bool(result.findings) != (result.action is expected):
        raise ValueError
    if result.text != (None if result.action is Action.BLOCK else prompt):
        raise ValueError
    codes: list[str] = []
    for finding in result.findings:
        if (
            not isinstance(finding, Finding)
            or type(finding.code) is not str
            or finding.code not in SECRET_CODES
        ):
            raise ValueError
        codes.append(finding.code)
    return result.action.value, codes


def handle_event(
    raw: bytes,
    *,
    profile: str = "advisory",
    scanner: Callable[[str, bool, str], Result] | None = None,
) -> Outcome:
    """Check only the submitted prompt and request a decision without host claims."""
    if type(profile) is not str or profile not in PROFILES:
        return _outcome("unavailable", "invalid_configuration", profile=None)
    if not isinstance(raw, bytes):
        return _outcome("invalid_event", "invalid_json", profile=profile)
    if len(raw) > MAX_EVENT_BYTES:
        return _outcome("invalid_event", "event_too_large", profile=profile)
    try:
        event = runtime.decode_event(raw)
    except (ValueError, UnicodeError, RecursionError):
        return _outcome("invalid_event", "invalid_json", profile=profile)
    if not isinstance(event, dict):
        return _outcome("invalid_event", "invalid_event", profile=profile)
    event_name = event.get("hook_event_name")
    if not isinstance(event_name, str) or not event_name:
        return _outcome("invalid_event", "invalid_event", profile=profile)
    if event_name != "beforeSubmitPrompt":
        return _outcome("unsupported", "unsupported_event", profile=profile)
    # Ignored event metadata is never scanned, opened, logged or returned.
    prompt = event.get("prompt")
    if not isinstance(prompt, str):
        return _outcome("invalid_event", "invalid_event", profile=profile)
    if len(prompt) > MAX_PROMPT_CHARS:
        return _outcome("unavailable", "prompt_too_large", profile=profile)
    try:
        prompt.encode("utf-8")
    except UnicodeError:
        return _outcome("invalid_event", "invalid_event", profile=profile)
    try:
        version = metadata.version("guardtrellis")
    except Exception:
        return _outcome("unavailable", "runtime_unavailable", profile=profile)
    if type(version) is not str or version != EXPECTED_SDK_VERSION:
        return _outcome("unavailable", "sdk_version_mismatch", profile=profile)
    block_secrets = profile == "enforce-secrets-v1"
    try:
        result = (_scan_prompt if scanner is None else scanner)(prompt, block_secrets, "off")
    except ImportError:
        return _outcome(
            "unavailable",
            "runtime_unavailable",
            profile=profile,
            sdk_version=EXPECTED_SDK_VERSION,
        )
    except Exception:
        return _outcome(
            "unavailable",
            "scan_failed",
            profile=profile,
            sdk_version=EXPECTED_SDK_VERSION,
        )
    try:
        action, codes = _assess_result(result, prompt, block_secrets)
    except ImportError:
        return _outcome(
            "unavailable",
            "runtime_unavailable",
            profile=profile,
            sdk_version=EXPECTED_SDK_VERSION,
        )
    except Exception:
        return _outcome(
            "unavailable",
            "unexpected_scan_result",
            profile=profile,
            sdk_version=EXPECTED_SDK_VERSION,
        )
    if action == "error":
        return _outcome(
            "unavailable",
            "scan_failed",
            profile=profile,
            scanner_action="error",
            sdk_version=EXPECTED_SDK_VERSION,
        )
    return _outcome(
        "checked",
        "secret_detected" if codes else "clean_prompt",
        profile=profile,
        scanner_action=action,
        finding_codes=codes,
        sdk_version=EXPECTED_SDK_VERSION,
    )


def _fallback_pair(outcome: Outcome) -> tuple[str, str]:
    """A bounded literal fallback also works when JSON serialization itself fails."""
    profile = outcome.report.get("profile")
    if type(profile) is not str or profile not in PROFILES:
        profile = None
    profile_json = f'"{profile}"' if profile is not None else "null"
    continuing = profile == "advisory"
    response = (
        '{"continue":true}\n'
        if continuing
        else ('{"continue":false,"user_message":"' + UNAVAILABLE_MESSAGE + '"}\n')
    )
    sdk_json = '"0.1.9"' if outcome.report.get("sdk_version") == EXPECTED_SDK_VERSION else "null"
    report = (
        '{"contract":"cursor_prompt_v1","profile":'
        + profile_json
        + ',"boundary":"beforeSubmitPrompt.prompt","check_status":"unavailable",'
        '"policy_action":"'
        + ("warn" if continuing else "block")
        + '","scanner_action":null,"reason_code":"output_limit_exceeded",'
        '"finding_codes":[],"sdk_version":'
        + sdk_json
        + ',"requested_continue":'
        + ("true" if continuing else "false")
        + ',"host_enforcement":"not_observed"}\n'
    )
    return response, report


def _serialize(outcome: Outcome, *, diagnostics: str = "all") -> tuple[str, str]:
    try:
        response = json.dumps(outcome.response, ensure_ascii=True, allow_nan=False) + "\n"
        report = json.dumps(outcome.report, ensure_ascii=True, allow_nan=False) + "\n"
        if (
            len(response.encode("utf-8")) > MAX_RESPONSE_BYTES
            or len(report.encode("utf-8")) > MAX_REPORT_BYTES
        ):
            raise ValueError
        # Only suppress a complete clean result after successful bounded serialization.
        # The unavailable fallback below must always retain its diagnostic record.
        if (
            diagnostics == "findings"
            and set(outcome.response) == {"continue"}
            and outcome.response.get("continue") is True
            and outcome.report.get("check_status") == "checked"
            and outcome.report.get("policy_action") == "allow"
            and outcome.report.get("scanner_action") == "allow"
            and outcome.report.get("reason_code") == "clean_prompt"
            and outcome.report.get("finding_codes") == []
            and outcome.report.get("requested_continue") is True
        ):
            report = ""
        return response, report
    except Exception:
        return _fallback_pair(outcome)


def _emit(outcome: Outcome, *, diagnostics: str = "all") -> int:
    response, report = _serialize(outcome, diagnostics=diagnostics)
    if sys.stdout is None or sys.stderr is None:
        return 1
    for stream, serialized in ((sys.stdout, response), (sys.stderr, report)):
        if not serialized:
            continue
        try:
            if stream.write(serialized) != len(serialized):
                raise OSError
            stream.flush()
        except Exception:
            try:
                runtime._discard_failed_stream(stream)
            except Exception:
                pass
            return 1
    return 0


def _options(argv: Sequence[str]) -> tuple[str, str] | None:
    options = {"--profile": "advisory", "--diagnostics": "all"}
    seen: set[str] = set()
    index = 0
    while index < len(argv):
        option, separator, value = argv[index].partition("=")
        if option not in options or option in seen:
            return None
        seen.add(option)
        if not separator:
            index += 1
            if index == len(argv):
                return None
            value = argv[index]
        options[option] = value
        index += 1
    profile, diagnostics = options["--profile"], options["--diagnostics"]
    if profile not in PROFILES or diagnostics not in DIAGNOSTICS:
        return None
    return profile, diagnostics


def main(argv: Sequence[str] | None = None) -> int:
    options = _options(sys.argv[1:] if argv is None else argv)
    if options is None:
        return _emit(_outcome("unavailable", "invalid_configuration", profile=None))
    profile, diagnostics = options
    try:
        raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
        if not isinstance(raw, bytes):
            raise OSError
    except Exception:
        return _emit(
            _outcome("unavailable", "stream_unavailable", profile=profile),
            diagnostics=diagnostics,
        )
    return _emit(handle_event(raw, profile=profile), diagnostics=diagnostics)


if __name__ == "__main__":
    raise SystemExit(main())
