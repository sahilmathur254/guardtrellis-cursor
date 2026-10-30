# GuardTrellis for Cursor — reviewer guide

Experimental macOS developer preview using SDK **0.1.9**. The verified user workflow is explicit Terminal preparation → reviewed Cursor draft → Cancel. Preparation masks selected email/phone patterns and withholds recognized secret signatures or unavailable checks. Names and unsupported patterns can remain. Ordinary chat is not automatically rewritten.

The bundled prompt hook is advisory by default: findings and unavailable checks request continuation. Its actual submitted-prompt runtime/decisions, stable trust, failures/bypasses and downstream effects remain unverified on the named current build. No native enforcement or provider-egress claim is made. Do not send prompts merely to complete this guide.

## 1. Establish exact source and artifacts

Review the source selected for the application, README, PUBLIC-EVIDENCE, [service terms](TERMS.md), [security reporting](SECURITY.md), compatibility, privacy and support. The 30 October policy refresh is a documentation-only source update. Application-time source was 1ebfd6a, followed by the README-only public update c66b16e; those earlier snapshots do not include these policies. The current source has local offline validation; GitHub CI remains bound to 1ebfd6a. Source availability does not establish a downloadable release, reindex result, marketplace approval or listing. The full terms and incident procedure ship inside both SUPPORT.md copies; earlier website policies cover other offerings. Use only the matching complete helper delivery and independently trusted full checksum. The native ZIP does not contain the workspace installer. Source publication, a downloadable release, review approval and marketplace availability are separate states.

The native/helper copy refresh changes documentation and derived source-manifest/inner-pin metadata only; their artwork, plugin/hook manifests, implementation and SDK locks remain unchanged. The separate publisher SVG and this guide are outside those archives. See PUBLIC-EVIDENCE for exact mapping. Accepted implementation evidence is tied to exact older archive hashes there; new artifact hashes and unchanged implementation mappings must be checked separately. Do not represent the revised whole ZIP as a new native trial or the earlier CI run as current-source CI.

If no matching downloadable helper has been published, build it from the exact reviewed public source with an existing trusted Python; no SDK install/editor/provider is needed for packaging. Replace these placeholders, choose a fresh output path and compare the resulting checksums to PUBLIC-EVIDENCE:

```sh
GT_PY="/absolute/trusted/python3.12"
GT_SOURCE="/absolute/reviewed-guardtrellis-cursor-source"
GT_OUTPUT="/absolute/fresh-source-build-output"
GT_NATIVE_SHA="1dd58f7d6d165db44708608f608691c4945a4ef719dd6ffafe6f7a500bcb691b"
GT_HELPER_SHA="0bdf1726eabdc36e6f3ed270d9a5c18bd13887c9e330aa4be06895c07d64a82a"

"$GT_PY" -I -B "$GT_SOURCE/scripts/cursor_release.py" build \
  --source "$GT_SOURCE" --output "$GT_OUTPUT/native" --profile advisory
"$GT_PY" -I -B "$GT_SOURCE/scripts/cursor_release.py" verify \
  "$GT_OUTPUT/native/guardtrellis-cursor-0.1.0-preview.4-advisory.zip" \
  --sha256 "$GT_NATIVE_SHA"
"$GT_PY" -I -B "$GT_SOURCE/scripts/cursor_delivery.py" build \
  --source "$GT_SOURCE" --output "$GT_OUTPUT/helper" \
  --native-archive "$GT_OUTPUT/native/guardtrellis-cursor-0.1.0-preview.4-advisory.zip" \
  --native-sha256 "$GT_NATIVE_SHA"
"$GT_PY" -I -B "$GT_SOURCE/scripts/cursor_delivery.py" verify \
  "$GT_OUTPUT/helper/guardtrellis-cursor-helper-0.1.0-preview.4.zip" \
  --sha256 "$GT_HELPER_SHA"
```

Stop on a mismatch or unavailable check; do not substitute an older tester ZIP. The reviewed source/commit and trusted checksums are separate from an unknown downloaded script. Continue with the matching outer guide for extraction and setup.

## 2. Prepare an owned local environment

Follow the complete helper README with a trusted existing Python 3.12 and uv, authenticated native source, fresh canonical retained-tools/runtime paths and an unopened synthetic workspace. Setup is explicit and may use package registries; no GuardTrellis account/API key/hosted service/MCP is needed. Keep the runtime external to workspace/plugin source. Review helper `plan` before `install`, then `health --check-runtime` and runtime `doctor`.

These local checks do not prove that the editor loaded the plugin. Staging one workspaceOpen entry is separate from activation. Opening/reloading the selected workspace can execute it. Use an explicitly approved test instance/profile and review inherited HOME hooks/skills/managed settings; separate storage is not a full HOME or network sandbox. Native loading requires its own observed result.

## 3. Run synthetic local preparation first

Run this in Terminal, using authenticated retained native tools and the prepared runtime, never Agent Chat:

```sh
GUARDTRELLIS_CURSOR_RUNTIME="$gt_runtime" \
  /bin/sh "$gt_native_tools/scripts/guardtrellis.sh" prepare <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

Expected stdout is `Repeat after me: Mira [PII] [PII].` with fixed metadata on stderr. A recognized synthetic GitHub token shape (`ghp_` plus 36 lowercase `a` characters) must withhold the entire prepared draft, including mixed secret/PII input. Local secret withholding is not a native prompt cancellation or measured downstream block. Missing/wrong runtime must be unavailable, with no automatic install or interpreter fallback.

## 4. Optional isolated native review and Cancel

This is an editor action and needs its own explicit activation/test scope. Keep the installed Cursor build fixed and use an already-open intended empty test workspace, with explicit existing canonical separate user-data/extensions directories/profile. Choose a short user-data path on macOS: the accepted test used a socket path of 52 characters; a long scratch path previously exceeded the installed build's 103-character IPC limit before workspace loading.

```sh
GUARDTRELLIS_CURSOR_RUNTIME="$gt_runtime" \
  /bin/sh "$gt_native_tools/scripts/guardtrellis.sh" prepare --open \
  --user-data-dir "$gt_cursor_user_data" \
  --extensions-dir "$gt_cursor_extensions" \
  --cursor-profile "$gt_cursor_profile" <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

Observe the exact masked text in Cursor's native review, verify the intended window/workspace/context, then press **Escape/Cancel**. Confirm the dialog disappears and New Agent input stays empty. Do not click Create Chat, Send, sign in or invoke an agent slash command. The target tuple and CLI exit 0 request routing; they do not prove the exact workspace or successful review. Failure/timeout can follow handoff; inspect before a deliberate manual retry. No automatic fallback/retry exists.

The actual product path was observed on Cursor 3.27.22/macOS 27.0.1 arm64 with SDK 0.1.9/Python 3.12.0, after native loading was confirmed. This is named-build evidence, not every-window/platform/version or complete egress suppression. [Official deeplink behavior](https://cursor.com/docs/reference/deeplinks) requires review; `--open-url` is named shipped-CLI compatibility, not a general-version guarantee.

## 5. Remove only owned state

Close only the verified owned test process. Use the matching helper's `remove` to retire the recognized workspace entry/source while preserving unrelated hooks/mode and the external runtime. Fresh native absence is a separate close/remove/reopen observation, not immediate live unload. Use retained verified tools for the later explicit unused-owned-runtime `doctor`/`remove`; do not call a deleted workspace script, force unknown ownership or delete a shared environment.

## Support and remaining coverage

Use the native support/privacy/compatibility documents and the monitored public contact [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com). Support is manual with no response-time SLA. Send only reviewed metadata/status codes and fictional reproduction to the confirmed public support contact; no raw prompts/source, match values, host debug logs, account/session IDs, private paths, environment dumps or credentials. No automatic collector/upload/export is provided.

Attachments, history, indexing, file reads, shell/MCP calls, inline completion, Cmd+K and other agents are outside coverage. Native Windows/Linux and enterprise management are outside this first preview. Ordinary marketplace installation/update/removal will be checked when that distribution route is available. No vendor approval or turnaround is guaranteed.
