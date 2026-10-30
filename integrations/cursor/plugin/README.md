# GuardTrellis for Cursor — experimental native source

**0.1.0-preview.4 · SDK 0.1.9 · advisory by default.** This is a local candidate, not a marketplace listing or a new public download. It contains selected-secret prompt-check code, explicit local runtime tools and Terminal email/phone preparation. It needs no GuardTrellis account, API key, MCP server or hosted scanner.

**The accepted runtime has bounded native evidence.** Advisory preview.4 SHA `a655171ed0ef3416baa0553d6afac9fd0f3954c1cfdfdea4f0b5502a800ad45f` was observed on Cursor **3.27.22 / macOS 27.0.1 arm64, Python 3.12.0**: native plugin loading first, actual installed shell/full-target prefill, masked email/phone review, automated Escape/empty input, cold reopen **1 loaded / 0 retained / 0 failures** and fresh post-removal **0 loaded / 0 retained / 0 failures**. No callback override, Create Chat, Send or provider/model workflow was used. This documentation-only refresh corrects the pre-trial status and creates new checksums; its new ZIP is not itself whole-package host-tested. Behavior evidence maps to unchanged executable/configuration/runtime inputs from the accepted archive. Prior preview.3 callback-based masked review/owner-assisted Cancel and earlier preview.2 evidence remain historical. Native prompt-hook SDK consumption/decisions, stable trust, failures/bypasses, downstream requests and ordinary marketplace installation remain unverified.

## Behavior and coverage

The selected advisory hook checks only `beforeSubmitPrompt.prompt` for GitHub classic/fine-grained token shapes, AWS access-key IDs and PEM private-key signatures. **A finding or unavailable check requests continuation.** This source does not provide a demonstrated secret-blocking workflow. A separately scoped enforcing artifact requires deliberate review and its own acceptance; do not change a live hook to obtain it.

A scanner finding, requested cancellation, cancellation UI and an observed blocked downstream request are different observations. Cursor may use prompt content for naming before the hook and retain original hook input/history. No complete prompt-egress or model-request suppression is claimed.

The prompt hook does not rewrite prompts. Ordinary chat has PII checking/redaction off. The separate Terminal `prepare` command masks selected email and contiguous international-phone shapes for review; names and unsupported forms can remain. Secrets or unavailable/error checks withhold the draft. Attachments, conversation history, indexing, file reads, shell/MCP calls, inline completion, Cmd+K and other agents are outside coverage.

GuardTrellis diagnostics omit input/match values. Preparation intentionally emits checked text to stdout; the host, shell or tools may retain it. Read [privacy](PRIVACY.md), [support](SUPPORT.md) and [compatibility](COMPATIBILITY.md).

## Source and runtime identities

| Item | Identity and limit |
| --- | --- |
| Native source / complete helper delivery | 0.1.0-preview.4; separate source artifacts |
| SDK | Locked GuardTrellis 0.1.9; scanner implementations are reused through public SDK APIs |
| Existing runtime marker/default identity | `0.1.0-preview.1-sdk0.1.9`, intentionally retained |
| Declared Python range | 3.11–3.14; prior named local/host evidence used Python 3.12.0 |
| Intended initial host | macOS arm64, named Cursor desktop build; native Windows/Linux and other combinations are not advertised |

The runtime identity is independent of the documentation/package version. Keeping its tag avoids silently changing a default environment or migrating the working demo. It does **not** authorize reusing/removing an unknown environment merely because its tag or SDK matches. Setup requires a fresh destination; use the explicit doctor and ownership record when reviewing any existing environment. Prompt handling never downloads dependencies, installs Python or falls back to another interpreter.

## Deliberate setup with the complete helper bundle

This 23-member native ZIP does **not** contain the workspace installer. Obtain the matching complete helper bundle and authenticate its outer checksum through a trusted publisher channel before extracting/executing it. Follow its outer README for strict verification. Keep the verified bundle and an external native-tools copy for recovery; do not put the inner ZIP directly into a normal plugin cache.

Run the following shapes in **Terminal**, not Agent Chat. Replace all placeholders. Use an existing trusted Python 3.12 and uv; the prior named tool was uv 0.8.17. Choose an existing, unopened, approved workspace and fresh canonical, unlinked native-tools/runtime paths. Keep workspace, tools and runtime separate from each other and outside the extracted helper bundle and IDE profiles.

```sh
GT_PY="/absolute/trusted/python3.12"
GT_UV="/absolute/trusted/uv"
GT_HELPER_ROOT="/absolute/verified-helper-bundle"
GT_WORKSPACE="/absolute/approved workspace with spaces"
GT_NATIVE_ZIP="$GT_HELPER_ROOT/artifacts/guardtrellis-cursor-0.1.0-preview.4-advisory.zip"
GT_NATIVE_SHA="REPLACE_WITH_TRUSTED_NATIVE_SHA256"
GT_NATIVE_TOOLS="/absolute/new-retained-native-tools"
GT_RUNTIME="/absolute/new-external-sdk019-runtime"
GT_HELPER="$GT_HELPER_ROOT/scripts/cursor_workspace.py"

"$GT_PY" -I -B "$GT_HELPER_ROOT/scripts/cursor_release.py" \
  extract "$GT_NATIVE_ZIP" --sha256 "$GT_NATIVE_SHA" --dest "$GT_NATIVE_TOOLS"
"$GT_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" \
  setup --python "$GT_PY" --uv "$GT_UV" --dest "$GT_RUNTIME"
"$GT_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" doctor --dest "$GT_RUNTIME"
```

Initial explicit setup may fetch locked packages from PyPI/distribution hosts unless a complete cache and offline mode are supplied. Those services receive ordinary request metadata. Setup is separate from provider/model use and activates no host. The default runtime path remains `~/Library/Application Support/GuardTrellis/Cursor/0.1.0-preview.1-sdk0.1.9`; the explicit path above is preferable for a separately scoped trial.

Review a concrete read-only plan before staging the selected project's hook:

```sh
"$GT_PY" -I -B "$GT_HELPER" plan \
  --workspace "$GT_WORKSPACE" --archive "$GT_NATIVE_ZIP" --sha256 "$GT_NATIVE_SHA" \
  --python "$GT_PY" --runtime "$GT_RUNTIME"
```

After reviewing the plan and approving this selected project's configuration change:

```sh
"$GT_PY" -I -B "$GT_HELPER" install \
  --workspace "$GT_WORKSPACE" --archive "$GT_NATIVE_ZIP" --sha256 "$GT_NATIVE_SHA" \
  --python "$GT_PY" --runtime "$GT_RUNTIME"
"$GT_PY" -I -B "$GT_HELPER" health --workspace "$GT_WORKSPACE"
"$GT_PY" -I -B "$GT_HELPER" health --workspace "$GT_WORKSPACE" --check-runtime
```

Install stages `.guardtrellis-cursor/` and one hash-bound `workspaceOpen` command in `.cursor/hooks.json`; it preserves unrelated valid hooks, order, fields and file permissions. Extraction/runtime setup, staged configuration and observed host activation are different states. Existing control trees, modified/unknown/linked ownership and malformed or duplicate-key JSON are refused. There is no force update or move/retarget operation.

Health is local. The optional runtime check runs synthetic SDK probes; unavailable runtime returns nonzero while configuration state stays separate. CLI health does not inspect native activation, GUI environment, trust or downstream traffic.

## Activation and runtime handoff are separate

Opening/reloading a staged workspace can execute its project lifecycle hook immediately. Use only the separately approved workspace/process/profile procedure. Do not activate a normal profile as an unqualified substitute for the earlier isolated trial. Separate user-data/extensions/profile storage does not hide OS-home hooks, shared caches or managed policy; report disabled/untrusted/unavailable state honestly.

`--runtime` records the external reference; it does not configure a running GUI. A later approved new Cursor process must receive `GUARDTRELLIS_CURSOR_RUNTIME` with the same path, or use a separately prepared verified default runtime. A Terminal export does not update an already running app. The bootstrap validates its owned source/configuration and returns a fixed path independently of SDK availability; loading alone is not active scanning.

## Check masking locally before any editor action

Use synthetic data through stdin:

```sh
GUARDTRELLIS_CURSOR_RUNTIME="$GT_RUNTIME" \
  /bin/sh "$GT_NATIVE_TOOLS/scripts/guardtrellis.sh" prepare <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

Expected checked text is `Repeat after me: Mira [PII] [PII].` The name remains. Metadata goes to stderr. Never put private text into chat, a slash command, an argument or an attachment to invoke masking.

## Request a reviewed draft in an explicit target

This separate editor action requires activation approval for the selected instance. Use an already-open approved Cursor instance/workspace with an empty draft and the selected existing canonical user-data/extensions directories. Those directories must be distinct, nonoverlapping and outside normal IDE roots. A named profile alone does not isolate user-data. Do not create or switch a normal profile as a shortcut.

```sh
GT_CURSOR_USER_DATA="/absolute/approved-existing-cursor-user-data"
GT_CURSOR_EXTENSIONS="/absolute/approved-existing-cursor-extensions"
GT_CURSOR_PROFILE="GuardTrellis-Isolated"
GUARDTRELLIS_CURSOR_RUNTIME="$GT_RUNTIME" \
  /bin/sh "$GT_NATIVE_TOOLS/scripts/guardtrellis.sh" prepare --open \
  --user-data-dir "$GT_CURSOR_USER_DATA" \
  --extensions-dir "$GT_CURSOR_EXTENSIONS" \
  --cursor-profile "$GT_CURSOR_PROFILE" <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

On macOS, choose a short canonical user-data path: IPC socket path limits can reject an otherwise valid directory before workspace loading. Directory validation alone does not guarantee that the host socket path fits.

The complete target is mandatory; bare `prepare --open` and partial/unknown options are refused. Accepted checked text alone is passed to the fixed `/Applications/Cursor.app/Contents/Resources/app/bin/cursor` desktop CLI, with a minimal local environment. There is no OS-opener/default-profile fallback or automatic retry. The tool does not press Send. Cursor may launch if the selected instance is closed; this is not a no-activation check.

[Cursor's prompt deeplink](https://cursor.com/docs/reference/deeplinks) opens a review and has a 10,000-character encoded-URL limit. The shipped Cursor 3.27.22 CLI recognizes `--open-url`; support across other builds is not guaranteed. Explicit directories/profile request the target, not the precise workspace/window. Inspect masked text, destination and attached context, and Cancel on wrong routing or a valuable draft. Review/Create Chat is not Send. This does not sanitize attachments/history or prove provider suppression. An error/timeout can happen after a handoff; inspect the instance before a deliberate manual retry. The accepted runtime’s actual product path was observed through review/automated Escape in the named isolated host; this does not establish submitted-prompt behavior or certify a changed executable.

## Safe removal, updates and rollback

Close the entire owned Cursor process first. With the retained complete helper bundle, remove only its recognized project state:

```sh
"$GT_PY" -I -B "$GT_HELPER" remove --workspace "$GT_WORKSPACE"
```

The helper preserves unrelated hooks and its external runtime; it reports native unload unobserved and restart required. A separately approved fresh process must verify the plugin no longer loads. Editing/removing config alone is not a reliable live unload. Removal does not erase host/provider history.

After confirming the runtime is unused elsewhere, use the **retained verified native-tools** copy, not the script removed with the project source:

```sh
"$GT_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" doctor --dest "$GT_RUNTIME"
"$GT_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" remove --dest "$GT_RUNTIME"
```

Keep matching artifacts/tools until recovery is verified. Updates/rollback use reviewed remove/reinstall and a new verified candidate identity; do not silently replace live source, default runtimes or older versioned downloads. Refused ownership/inventory/concurrent-state checks require local inspection; never use broad deletion or edit a ledger to force success. Neither helper starts Cursor, submits a prompt, changes trust, uploads support data or publishes a plugin automatically.

Support: [private reporting and metadata-only template](SUPPORT.md). Official routes: [workspace lifecycle hook](https://cursor.com/docs/hooks#workspaceopen), [project plugin loading](https://cursor.com/docs/plugins#using-the-workspaceopen-hook). Marketplace source, owner disclosure, exact-package host acceptance and curated review/publication are separate gates.

## Service terms, support and security

Read the packaged [service terms](SUPPORT.md#service-terms), [support data handling](SUPPORT.md#support-data-handling) and [publisher incident procedure](SUPPORT.md#publisher-incident-procedure). They cover this native/helper preview and publisher support; older website offerings have separate policies. Publisher responsibilities remain applicable despite the experimental scope and absence of a response-time SLA. No outreach, incident or marketplace approval is implied by these documents.
