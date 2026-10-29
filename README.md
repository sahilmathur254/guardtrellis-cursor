<p align="center">
  <img src="assets/publisher-logo.svg" alt="GuardTrellis" width="160">
</p>

# GuardTrellis for Cursor

Prepare a checked draft locally, then review it in Cursor.

Built on the [GuardTrellis Python SDK](https://pypi.org/project/guardtrellis/), this companion adds selected email/phone masking, recognized-secret checks and a deliberate review workflow for Cursor.

[SDK on PyPI](https://pypi.org/project/guardtrellis/) · [SDK source](https://github.com/sahilmathur254/guardtrellis) · [Setup guide](integrations/cursor/delivery/README.md) · [Reviewer guide](REVIEWER.md)

> **Experimental macOS preview.** The Cursor marketplace application was submitted on 30 October 2026. Approval and listing have not been verified; no release download is published. Use the reviewed source and the guides below.

## What it does

| Workflow | Result |
| --- | --- |
| Prepare text in Terminal | Checks selected secret signatures first, then masks selected email and contiguous international-phone patterns. |
| Withhold on a secret or check failure | A recognized secret, check error or unavailable runtime prevents the prepared draft from being emitted or opened. |
| Review in Cursor | Explicitly opens accepted text in Cursor's native review. You inspect the draft and decide whether to send. The helper never presses Send. |
| Manage a selected workspace | Provides explicit setup, health checks and removal with ownership checks that preserve unrelated configuration. |

**Ordinary Cursor chat is not automatically redacted.** Masking uses the explicit Terminal preparation workflow. The included prompt hook is advisory: findings and unavailable checks request continuation, and its native submitted-prompt behavior remains unverified.

## Masking example

```text
Before: Repeat after me: Mira mira@example.org +12025550123.
After:  Repeat after me: Mira [PII] [PII].
```

The name remains. Unsupported formats and other personal information can remain too; selected patterns do not provide complete PII or secret detection.

## Get started

Use an existing trusted **Python 3.12** and **uv 0.8.17** for the documented setup. The declared Python range is 3.11–3.14; the named host tests used Python 3.12.

1. Read the [compatibility](plugins/guardtrellis-cursor/COMPATIBILITY.md), [privacy](plugins/guardtrellis-cursor/PRIVACY.md) and [support](plugins/guardtrellis-cursor/SUPPORT.md) documents.
2. [Build the matching archives from reviewed source](REVIEWER.md#1-establish-exact-source-and-artifacts), then follow the [complete helper setup guide](integrations/cursor/delivery/README.md). It covers trusted checksums, an external SDK runtime, workspace staging, health checks and removal. The native ZIP alone does not contain the workspace installer.
3. Test preparation locally in **Terminal**, using the paths configured by that guide:

```sh
GUARDTRELLIS_CURSOR_RUNTIME="$GT_CURSOR_RUNTIME" \
  /bin/sh "$GT_NATIVE_TOOLS/scripts/guardtrellis.sh" prepare <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

Expected stdout: `Repeat after me: Mira [PII] [PII].` Fixed diagnostic metadata goes to stderr. Keep raw input on stdin; do not paste the shell command or private input into Agent Chat.

To open a reviewed draft, follow the [explicit Cursor prefill workflow](integrations/cursor/plugin/README.md#request-a-reviewed-draft-in-an-explicit-target). `prepare --open` requires all three target options: `--user-data-dir`, `--extensions-dir` and `--cursor-profile`. Inspect the actual window, workspace and attached context; Cancel if the destination is wrong. A timeout/error can follow a handoff, so inspect before retrying. There is no automatic retry or default-profile fallback.

Source extraction and runtime setup do not activate hooks. Opening an approved staged workspace can activate its lifecycle hook. Initial setup may download locked packages from registries; prompt handling never installs a runtime. On macOS, use a short user-data path to avoid host IPC socket limits.

## Verified scope

| Item | Recorded version |
| --- | --- |
| Native plugin and helper | `0.1.0-preview.4` |
| GuardTrellis SDK pin | `0.1.9` |
| Named Cursor build | `3.27.22` |
| Named host environment | macOS `27.0.1`, arm64, Python `3.12.0` |

The accepted runtime was observed loading in Cursor, opening the masked review through the actual installed command, cancelling to an empty draft, reopening and being removed. Refreshed archives retain that runtime but have not undergone a new whole-package host trial. See the [exact hashes, runtime mapping and evidence limits](PUBLIC-EVIDENCE.md#accepted-preview4-runtime-and-documentation-refresh--29-october-2026).

[Manual CI at `1ebfd6a`](https://github.com/sahilmathur254/guardtrellis-cursor/actions/runs/40936455108) passed **146 tests, zero skips and all four phases**, including the SDK/helper lifecycle. CI process checks and actual IDE behavior are separate evidence.

This preview does not establish native prompt enforcement, stable host trust/failure/bypass behavior, downstream request blocking or complete prompt-egress prevention. Attachments, conversation history, indexing, file/shell/MCP activity, inline completion and other agents are outside coverage. Native Windows/Linux support is not advertised.

## How this relates to the SDK

The [GuardTrellis SDK on PyPI](https://pypi.org/project/guardtrellis/) provides the reusable checking engine and works independently of Cursor. This repository adds host adapters, reviewed prefill, installation helpers, packaging and host verification; it reuses SDK public APIs rather than copying scanner implementations.

SDK and companion versions are independent. This preview pins SDK **0.1.9**; installing the SDK alone does not install the Cursor integration. No hosted scanner, account system, MCP service or enterprise management layer is included. Historical `adapters/codex/` paths are shared-runtime compatibility names, not a Codex host integration.

## Support and contributing

Maintained by **Sahil Mathur** as an individual publisher. Public support/security contact: [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com). Support is manual, with no response-time SLA or automatic collection/upload.

Share reviewed version/status metadata and fictional reproductions only. Do not send raw prompts, source, matched values, credentials or host logs. Local preparation does not change Cursor/provider retention or network behavior. Older website/tester downloads retain their own version scope.

[Support and removal](plugins/guardtrellis-cursor/SUPPORT.md) · [Privacy](plugins/guardtrellis-cursor/PRIVACY.md) · [Maintenance and contribution workflow](MAINTAINING.md) · [License](LICENSE) · [Notices](NOTICE)
