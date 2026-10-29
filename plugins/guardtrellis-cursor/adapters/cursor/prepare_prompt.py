"""Prepare a reviewed local draft; an explicit --open requests Cursor prefill only."""

from __future__ import annotations

import json
import os
import re
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


CURSOR_CLI = "/Applications/Cursor.app/Contents/Resources/app/bin/cursor"
LAUNCH_ENV_KEYS = (
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "GUARDTRELLIS_CURSOR_RUNTIME",
)


@dataclass(frozen=True)
class LaunchTarget:
    user_data_dir: Path = field(repr=False)
    extensions_dir: Path = field(repr=False)
    profile: str = field(repr=False)


def _overlaps(first: Path, second: Path) -> bool:
    # samefile also detects case aliases on a case-insensitive volume. Known
    # protected roots can be absent; lexical protection still applies to them.
    if first.is_relative_to(second) or second.is_relative_to(first):
        return True
    for parent, child in ((first, second), (second, first)):
        for ancestor in (child, *child.parents):
            try:
                if ancestor.samefile(parent):
                    return True
            except FileNotFoundError:
                continue
    return False


def launch_target(user_data_dir: str, extensions_dir: str, profile: str) -> LaunchTarget:
    """Validate explicit existing storage; never create or edit a host/profile."""
    home = Path.home().resolve()
    protected = [
        home / ".cursor",
        home / ".codex",
        home / ".claude",
        home / "Library/Application Support/Cursor",
        home / "Library/Application Support/Code",
        Path("/Library/Application Support/Cursor"),
        Path("/Applications/Cursor.app"),
    ]
    directories = []
    for value in (user_data_dir, extensions_dir):
        if len(value) > 4096 or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError
        path = Path(value)
        if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_dir():
            raise ValueError
        if any(_overlaps(path, root) for root in protected):
            raise ValueError
        directories.append(path)
    data, extensions = directories
    if _overlaps(data, extensions):
        raise ValueError
    if (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}", profile) is None
        or profile != profile.strip()
    ):
        raise ValueError
    return LaunchTarget(data, extensions, profile)


def _launch(uri: str, target: LaunchTarget) -> bool:
    # Revalidate at dispatch. This is not a sandbox or a filesystem-race guarantee.
    target = launch_target(str(target.user_data_dir), str(target.extensions_dir), target.profile)
    env = {key: os.environ[key] for key in LAUNCH_ENV_KEYS if key in os.environ}
    env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
    completed = subprocess.run(
        [
            CURSOR_CLI,
            "--user-data-dir",
            str(target.user_data_dir),
            "--extensions-dir",
            str(target.extensions_dir),
            "--profile",
            target.profile,
            "--open-url",
            uri,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd=str(target.user_data_dir),
        check=False,
        timeout=LAUNCH_TIMEOUT_SECONDS,
    )
    return completed.returncode == 0


def _options(options: list[str]) -> tuple[bool, LaunchTarget | None]:
    if not options:
        return False, None
    if len(options) != 7 or options[0] != "--open":
        raise ValueError
    values = {}
    allowed = {"--user-data-dir", "--extensions-dir", "--cursor-profile"}
    for key, value in zip(options[1::2], options[2::2], strict=True):
        if key not in allowed or key in values:
            raise ValueError
        values[key] = value
    if set(values) != allowed:
        raise ValueError
    return True, launch_target(
        values["--user-data-dir"], values["--extensions-dir"], values["--cursor-profile"]
    )


def prepare_prompt(
    raw: bytes,
    *,
    open_cursor: bool = False,
    platform: str | None = None,
    launcher: Callable[[str], bool] | None = None,
    target: LaunchTarget | None = None,
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
        if launcher is not None:
            launched = launcher(uri)
        elif target is not None:
            launched = _launch(uri, target)
        else:
            report["reason_code"] = "invalid_configuration"
            return Prepared(None, report, 1)
        if launched is not True:
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
    try:
        open_cursor, target = _options(options)
    except Exception:
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
    return _emit(prepare_prompt(raw, open_cursor=open_cursor, target=target))


if __name__ == "__main__":
    raise SystemExit(main())
