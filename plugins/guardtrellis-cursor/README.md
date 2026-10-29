# GuardTrellis for Cursor — experimental native source

**0.1.0-preview.3 · SDK 0.1.9 · advisory by default.** This is a local candidate, not a marketplace listing or a new public download. It contains selected-secret prompt-check code, explicit local runtime tools and Terminal email/phone preparation. It needs no GuardTrellis account, API key, MCP server or hosted scanner.

**Preview.3 has not been tested in a real Cursor host.** This new local candidate corrects native-only notices and public copy; it changes package hashes while retaining the SDK, policy, helper/bootstrap and runtime/hook implementations. Earlier exact preview.2 loading/restart/removal and local SDK readiness/runtime binding were observed on Cursor 3.27.22/macOS arm64. Component UI and explicit-profile masked review → Cancel were separately observed in a named profile sharing application/account state. These are bounded preview.2 observations, not whole-package preview.3 acceptance. Native prompt-hook SDK consumption/decisions, stable trust, failures/bypasses, default opener, downstream requests and ordinary marketplace installation remain unverified.

## Behavior and coverage

The selected advisory hook checks only `beforeSubmitPrompt.prompt` for GitHub classic/fine-grained token shapes, AWS access-key IDs and PEM private-key signatures. **A finding or unavailable check requests continuation.** This source does not provide a demonstrated secret-blocking workflow. A separately scoped enforcing artifact requires deliberate review and its own acceptance; do not change a live hook to obtain it.

A scanner finding, requested cancellation, cancellation UI and an observed blocked downstream request are different observations. Cursor may use prompt content for naming before the hook and retain original hook input/history. No complete prompt-egress or model-request suppression is claimed.

The prompt hook does not rewrite prompts. Ordinary chat has PII checking/redaction off. The separate Terminal `prepare` command masks selected email and contiguous international-phone shapes for review; names and unsupported forms can remain. Secrets or unavailable/error checks withhold the draft. Attachments, conversation history, indexing, file reads, shell/MCP calls, inline completion, Cmd+K and other agents are outside coverage.

GuardTrellis diagnostics omit input/match values. Preparation intentionally emits checked text to stdout; the host, shell or tools may retain it. Read [privacy](PRIVACY.md), [support](SUPPORT.md) and [compatibility](COMPATIBILITY.md).

## Source and runtime identities

| Item | Identity and limit |
| --- | --- |
| Native source / complete helper delivery | 0.1.0-preview.3; separate source artifacts |
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
GT_NATIVE_ZIP="$GT_HELPER_ROOT/artifacts/guardtrellis-cursor-0.1.0-preview.3-advisory.zip"
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

Only a separate deliberate `prepare --open` requests Cursor's reviewed-prefill flow. It launches the editor and passes accepted text through OS/Cursor handling; it does not press Send. Start with an empty draft in the intended workspace/This Mac, inspect the text and attached context, and Cancel on a wrong destination or valuable existing draft. Review/Create Chat is not Send. This workflow does not sanitize attachments/history or prove provider-request suppression. The earlier preview.2 test used an explicit-profile CLI launcher callback and Cancel; it did not test the bundled default `/usr/bin/open -a` opener. No preview.3 native prefill acceptance or provider-suppression result is claimed.

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
