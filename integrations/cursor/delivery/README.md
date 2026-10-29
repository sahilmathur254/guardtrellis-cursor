# GuardTrellis Cursor workspace helper

Experimental delivery candidate, 29 October 2026. This bundle contains the complete local workspace helper and its verified **advisory** native plugin source. It is separate from the older tester kit and from the inner native-plugin ZIP. Creating or sharing this candidate does not establish a public release, source disclosure approval or marketplace listing.

**Native and delivery version: 0.1.0-preview.4. Accepted runtime evidence is bounded.** Advisory native SHA `a655171ed0ef3416baa0553d6afac9fd0f3954c1cfdfdea4f0b5502a800ad45f` and accepted helper SHA `63fc0224a78cd63fdb1f97ae965d21ea706ceb427ba65f5d6624f0fae5f3df25` were verified on Cursor 3.27.22/macOS 27.0.1 arm64/Python 3.12.0: native loading first, actual installed shell/full-target prefill, masked review, automated Escape/empty input, cold reopen 1/0/0 and fresh removal 0/0/0, no Create Chat/Send/provider workflow. This documentation-only refresh corrects the earlier status and produces new checksums with SDK 0.1.9/runtime tag unchanged. Its new archives are not themselves whole-package host-tested: behavior traces to the unchanged executable/configuration/runtime inventory from the accepted runtime. Prior preview.3 callback/owner-assisted Cancel and preview.2 evidence remain historical. Stable trust, native prompt decisions, failures/bypasses, downstream requests and ordinary marketplace installation remain unverified. Declared Python 3.11–3.14 is not a native tested matrix; native Windows/Linux is not advertised.

The hook checks selected GitHub-token, AWS access-key-ID and PEM-private-key signatures in the submitted prompt only. **This delivery is advisory:** it requests continuation on a finding or unavailable check. It does not install the separately scoped enforcing variant. A finding, requested cancellation and observed blocked downstream request are different outcomes. Ordinary prompt submission does not mask email or phone data. Attachments, history, indexing, file reads, shell/MCP calls, inline completion and other agents are outside coverage.

## What is included

The outer file is `guardtrellis-cursor-helper-0.1.0-preview.4.zip`. Its allowlisted contents are:

- `README.md`, `SUPPORT.md`, `LICENSE`, `NOTICE` and `DELIVERY-MANIFEST.json`.
- `scripts/cursor_delivery.py`, `scripts/cursor_workspace.py`, `scripts/cursor_release.py` and `integrations/cursor/bootstrap.py`.
- `artifacts/guardtrellis-cursor-0.1.0-preview.4-advisory.zip`, the 23-member native source archive (member count retained; prefill-route/documentation/version bytes refreshed).

The inner archive's SHA-256 is `092f10ac145838ffc25f11396b129b808bc5ed1f782cd9cb89da3c04758ae064`. Its native-specific README, compatibility, privacy and support documents describe preview.4's scope. Prior preview.2 bounded lifecycle/component/review observations remain dated evidence; they do not certify this new package. The bundle contains no Python, virtual environment, credentials, hosted service or automatic updater.

## 1. Authenticate and extract the outer bundle

Obtain the outer ZIP and its **full SHA-256 from a trusted publisher delivery channel**. A checksum copied from an unknown ZIP or its internal manifest does not authenticate that ZIP. Do not execute bundled Python or extract an unauthenticated archive.

In Terminal, replace the placeholders below. Use an existing trusted Python 3.12 executable and a fresh, absolute, unlinked extraction directory outside IDE profiles and the selected workspace/runtime.

```sh
GT_CURSOR_PY="/absolute/trusted/python3.12"
GT_DELIVERY_ZIP="/absolute/guardtrellis-cursor-helper-0.1.0-preview.4.zip"
GT_DELIVERY_SHA="REPLACE_WITH_TRUSTED_OUTER_64_HEX_SHA256"
GT_DELIVERY_ROOT="/absolute/new-guardtrellis-helper-bundle"

printf '%s  %s\n' "$GT_DELIVERY_SHA" "$GT_DELIVERY_ZIP" |
  /usr/bin/shasum -a 256 -c -
```

**Stop unless the checksum reports `OK`.** After that successful check, use standard-library extraction into a fresh directory, then run the bundled strict archive verifier:

```sh
mkdir "$GT_DELIVERY_ROOT" &&
  "$GT_CURSOR_PY" -I -B -m zipfile -e "$GT_DELIVERY_ZIP" "$GT_DELIVERY_ROOT"

"$GT_CURSOR_PY" -I -B "$GT_DELIVERY_ROOT/scripts/cursor_delivery.py" \
  verify "$GT_DELIVERY_ZIP" --sha256 "$GT_DELIVERY_SHA"
```

Stop on any nonzero exit, missing/extra member, manifest/hash mismatch or non-advisory result. Do not reuse an existing extraction directory. Operators who already have a trusted complete verifier closure can instead use its `extract ZIP --sha256 HEX --dest NEW_DIRECTORY` command; it verifies before extracting. Neither extraction route installs a project hook or activates Cursor.

## 2. Choose separate paths and prepare the explicit local runtime

Use an existing, **unopened** selected workspace. Close that workspace in Cursor before staging changes. All paths must be absolute, canonical and unlinked. Keep the workspace, external runtime and retained native-tools directory outside the extracted bundle and separate from each other. Do not choose a normal IDE profile, another integration's environment or a destination containing unknown files.

```sh
GT_WORKSPACE="/absolute/approved workspace with spaces"
GT_CURSOR_RUNTIME="/absolute/new-guardtrellis-sdk019-runtime"
GT_NATIVE_TOOLS="/absolute/new-verified-native-tools"
GT_UV="/absolute/trusted/uv"
GT_NATIVE_ZIP="$GT_DELIVERY_ROOT/artifacts/guardtrellis-cursor-0.1.0-preview.4-advisory.zip"
GT_NATIVE_SHA="092f10ac145838ffc25f11396b129b808bc5ed1f782cd9cb89da3c04758ae064"
GT_WORKSPACE_HELPER="$GT_DELIVERY_ROOT/scripts/cursor_workspace.py"

"$GT_CURSOR_PY" -I -B "$GT_DELIVERY_ROOT/scripts/cursor_release.py" \
  extract "$GT_NATIVE_ZIP" --sha256 "$GT_NATIVE_SHA" --dest "$GT_NATIVE_TOOLS"

"$GT_CURSOR_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" \
  setup --python "$GT_CURSOR_PY" --uv "$GT_UV" --dest "$GT_CURSOR_RUNTIME"
"$GT_CURSOR_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" \
  doctor --dest "$GT_CURSOR_RUNTIME"
```

Keep this verified native-tools copy for runtime removal after the workspace helper has removed its own source. The tested tool was uv 0.8.17. Runtime setup is deliberate: it may download locked packages from PyPI/distribution hosts unless a complete cache and `UV_OFFLINE=1` are supplied. It does not download Python or call an AI provider. Existing destinations are refused. The SDK pin stays 0.1.9; there is no automatic upgrade or fallback interpreter during prompt handling. The runtime marker/default identity intentionally remains `0.1.0-preview.1-sdk0.1.9`, independent of the native/delivery version. This prevents silent default-runtime redirection or migration; it is not permission to reuse or remove an existing environment merely because its tag matches. Choose a fresh explicit destination or review its owned record with doctor.

A successful doctor means local synthetic checks passed. It does not prove that a running GUI process uses this runtime, that hooks are trusted/enabled or that any downstream request was blocked. If setup is incomplete, preserve its ownership record and use the lifecycle tool's reviewed removal path; do not delete broad directories or retry over unknown state.

## 3. Review and stage only the selected project

Run `plan` first; it is read-only. It shows the exact managed entry, new file hashes and existing configuration hashes/counts without echoing other command values.

```sh
"$GT_CURSOR_PY" -I -B "$GT_WORKSPACE_HELPER" plan \
  --workspace "$GT_WORKSPACE" --archive "$GT_NATIVE_ZIP" --sha256 "$GT_NATIVE_SHA" \
  --python "$GT_CURSOR_PY" --runtime "$GT_CURSOR_RUNTIME"
```

Review the proposed diff and obtain the selected project's approval before changing its configuration. Only then run:

```sh
"$GT_CURSOR_PY" -I -B "$GT_WORKSPACE_HELPER" install \
  --workspace "$GT_WORKSPACE" --archive "$GT_NATIVE_ZIP" --sha256 "$GT_NATIVE_SHA" \
  --python "$GT_CURSOR_PY" --runtime "$GT_CURSOR_RUNTIME"
"$GT_CURSOR_PY" -I -B "$GT_WORKSPACE_HELPER" health --workspace "$GT_WORKSPACE"
"$GT_CURSOR_PY" -I -B "$GT_WORKSPACE_HELPER" health \
  --workspace "$GT_WORKSPACE" --check-runtime
```

The helper owns `<workspace>/.guardtrellis-cursor/` and one hash-bound `workspaceOpen` command in `.cursor/hooks.json`. Other valid hooks, their order, fields and configuration permissions are preserved; JSON formatting can change. `configuration_staged` is not an observed host activation. Health separates configuration readiness, the optional explicit runtime check and unobserved native/GUI state. A requested unavailable runtime check exits nonzero even when configuration remains ready.

Repeating install refuses the existing control tree rather than duplicating or overwriting it. Modified/unknown/linked ownership state or malformed/duplicate-key JSON is refused. Inspect that state locally; do not edit the ledger or disable checks to force success. Move/retarget is not implemented: remove from the original workspace before moving it.

## 4. Host activation is a separate action

Extraction, runtime setup and workspace helper operations never launch/reload Cursor or configure a running GUI environment. Opening an approved staged workspace can execute its lifecycle hook immediately. Obtain the selected project's activation approval and use a separately reviewed fresh-process/profile procedure before that action. Prior preview.3 lifecycle/component/review acceptance used separate owned user-data/extensions directories. Profiles do not hide all OS-home hooks, global caches, account state or managed policy. Check inherited sources and effective trust/policy rather than changing normal or managed controls to force loading.

`--runtime` binds the helper's external reference; it does not set the launcher's environment. A later approved **new process** must receive `GUARDTRELLIS_CURSOR_RUNTIME` with the same path, or use a separately prepared verified default runtime. Setting it in Terminal does not change an already running GUI app. Do not use a normal profile as an unqualified substitute for the isolated acceptance route. Local CLI health deliberately cannot attest the GUI environment.

This delivery/support batch does not perform activation, reload, Send, a provider request or marketplace import. A native loading result alone does not authorize an agent submission or establish enforcement. Cursor's own naming, history, logs and provider handling remain separate; no complete prompt-egress suppression is claimed.

## 5. Test masking locally, then review separately

This synthetic Terminal-only command needs the prepared runtime but does not need a prompt submission:

```sh
GUARDTRELLIS_CURSOR_RUNTIME="$GT_CURSOR_RUNTIME" \
  /bin/sh "$GT_NATIVE_TOOLS/scripts/guardtrellis.sh" prepare <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

Expected checked stdout is `Repeat after me: Mira [PII] [PII].` The name remains. Content-free status/finding metadata goes to stderr. Selected email and contiguous international-phone shapes are checked with secret signatures first; secrets, mixed secret/PII findings and unavailable/error states withhold the draft. Names, unsupported forms and other context can remain. Raw input belongs on stdin, never in agent chat, a slash command, an argument or an attachment.

A separate later-authorized editor action requires this complete explicit target:

```sh
GT_CURSOR_USER_DATA="/absolute/approved-existing-cursor-user-data"
GT_CURSOR_EXTENSIONS="/absolute/approved-existing-cursor-extensions"
GT_CURSOR_PROFILE="GuardTrellis-Isolated"
GUARDTRELLIS_CURSOR_RUNTIME="$GT_CURSOR_RUNTIME" \
  /bin/sh "$GT_NATIVE_TOOLS/scripts/guardtrellis.sh" prepare --open \
  --user-data-dir "$GT_CURSOR_USER_DATA" \
  --extensions-dir "$GT_CURSOR_EXTENSIONS" \
  --cursor-profile "$GT_CURSOR_PROFILE" <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

On macOS, choose a short canonical user-data path: IPC socket path limits can reject an otherwise valid directory before workspace loading. Directory validation alone does not guarantee that the host socket path fits.

Use existing canonical distinct nonoverlapping user-data/extensions directories outside normal IDE roots. Bare `prepare --open`, partial/unknown options and unsafe paths are refused. The fixed installed desktop CLI receives only accepted checked text and a minimal environment, without OS-opener/default-profile fallback or automatic retry. The selected instance may launch if closed; this is **not run as part of bundle verification**.

[Official prompt deeplinks](https://cursor.com/docs/reference/deeplinks) require review. The shipped Cursor 3.27.22 CLI recognizes `--open-url`; no general version or exact destination workspace/window guarantee follows. Start with the already-open approved intended workspace/This Mac and empty draft; inspect masked text plus attachments/context, and Cancel if wrong. Review/Create Chat is not Send. A timeout/error can happen after handoff, so inspect before a deliberate manual retry. The accepted runtime’s actual product review/automated Escape is observed on the named isolated build; the new documentation-only ZIP has an exact runtime mapping rather than a new whole-package host trial. Earlier callback evidence remains historical. Ordinary chat cannot test automatic PII masking because the prompt hook does not rewrite prompts.

## 6. Remove, update and recover

Close the entire owned Cursor process first. Remove the workspace helper before deleting a runtime its hook could reference:

```sh
"$GT_CURSOR_PY" -I -B "$GT_WORKSPACE_HELPER" remove --workspace "$GT_WORKSPACE"
```

This removes only recognized owned source/control/entry, preserves unrelated configuration and reports restart required with native unload unobserved. A separately approved fresh native process must confirm the plugin no longer loads. Removal does not erase host/provider history.

The external runtime is deliberately still present. Only after confirming it is unused by other profiles/workspaces, use the **retained verified native-tools copy**, not the script just removed with the workspace source:

```sh
"$GT_CURSOR_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" \
  doctor --dest "$GT_CURSOR_RUNTIME"
"$GT_CURSOR_PY" -I -B "$GT_NATIVE_TOOLS/scripts/runtime_setup.py" \
  remove --dest "$GT_CURSOR_RUNTIME"
```

Keep matching artifacts/tools until cleanup or rollback is verified. For an update, review a new authenticated bundle/source/runtime identity, remove the previous owned installation safely and install into fresh reviewed state. There is no in-place force update or automatic migration. Rollback uses the retained accepted bundle/runtime and the same reviewed remove/install cycle; do not replace a live source cache or the older tester download silently. If ownership, inventory or concurrent-change checks refuse removal, stop and inspect; do not use `rm -rf`, delete a profile or alter unrelated hooks. See [support and the manually reviewed metadata template](SUPPORT.md).

Official route references: [Cursor workspace lifecycle hooks](https://cursor.com/docs/hooks#workspaceopen), [project plugin loading](https://cursor.com/docs/plugins#using-the-workspaceopen-hook). This source bundle adds no MCP service, enterprise management or listing approval.
