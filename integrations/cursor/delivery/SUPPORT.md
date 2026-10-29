# Support for the experimental Cursor helper bundle

Publisher: Sahil Mathur. Support is voluntary, with no response-time commitment, SLA or enterprise-management offer. This outer 0.1.0-preview.4 helper bundle is distinct from the inner 23-member native plugin ZIP and older tester download. Keep its authenticated ZIP/checksum and matching tools for reproduction and recovery.

Private support/security/privacy contact: [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com), published on the [support page](https://guardtrellis-plugin.sahil254.chatgpt.site/support/). That page was anonymously reachable on 29 October 2026; mailbox delivery/response and future availability are not promised. The public [privacy page](https://guardtrellis-plugin.sahil254.chatgpt.site/privacy/) still describes the older integration/site/email offering; the native-specific `PRIVACY.md` inside this bundle's included native ZIP and retained verified native-tools describes the preview.4 helper. Do not assume a public GitHub issue/advisory route exists or post private vulnerability details there. The tools do not open tickets, send email or upload diagnostics automatically.

## Evidence-bounded support matrix

| Area | Current evidence / limit |
| --- | --- |
| Host target | Accepted preview.4 runtime: native loading first, actual shell/full-target masked review, automated Escape/empty input, cold reopen 1/0/0 and fresh removal 0/0/0 on Cursor 3.27.22/macOS 27.0.1 arm64/Python 3.12.0; no Create Chat/Send/provider workflow. New documentation-only hashes are not themselves whole-package host-tested; unchanged executable/configuration mapping required |
| Runtime target | SDK 0.1.9; prior named Python 3.12.0 / uv 0.8.17. Runtime identity `0.1.0-preview.1-sdk0.1.9` intentionally remains independent of native/delivery 0.1.0-preview.4; no automatic reuse/migration |
| Delivery scope | Standalone allowlisted helper + builder + bootstrap + verified advisory native ZIP; no public release, marketplace or normal-profile acceptance implied |
| Policy | Advisory only; findings/unavailable checks request continuation. No enforcing profile is installed by this bundle |
| Prompt coverage | Selected secret signatures in submitted prompt only; actual native prompt-hook execution/decisions remain unverified for this candidate |
| PII masking | Explicit local Terminal email/contiguous-phone preparation; reviewed prefill is separate. Ordinary chat is not automatically masked |
| Not covered | Attachments/history/indexing/file reads/shell or MCP interception/inline completion/other agents; native Windows/Linux; complete egress suppression |
| Prior preview.2 | Historical lifecycle/UI/runtime/review observations; not changed-package acceptance |
| Still separate | Stable trust/disabled/failure/bypass behavior, native prompt-hook SDK consumption, downstream observation, ordinary marketplace installation and publication |

A scanner finding, a requested host cancellation and an observed blocked downstream request must be reported separately. Never test support claims with real credentials, personal data or confidential code. A free/trial account is not proof that a submission is nonbillable; support reproduction does not authorize provider usage.

Reviewed prefill now requires `--open --user-data-dir ABS --extensions-dir ABS --cursor-profile NAME`, with existing canonical distinct nonoverlapping directories outside normal IDE roots. Bare/partial options and unsafe paths are refused. Fixed installed desktop CLI/minimal environment replaces the unscoped OS opener; no default-profile fallback or automatic retry. Shipped Cursor 3.27.22 --open-url support is named-build compatibility, not a version or precise workspace/window guarantee. Check the already-open empty intended workspace, review and Cancel on wrong routing. Error/timeout can follow handoff; inspect before a manual retry. No Send/provider test follows from a support request.

## First checks in Terminal

Use the commands and absolute paths from [README.md](README.md). Run them outside agent chat; close the selected workspace before configuration changes.

- Check the outer archive against the independently trusted publisher SHA, then use its strict verifier. Confirm the exact inner advisory archive and helper/bootstrap fingerprints from the manifest; a locally generated checksum alone does not establish provenance.
- Run workspace `health` for source/config state. Add `--check-runtime` only when you want local synthetic SDK execution. Keep configuration-ready and runtime-unavailable results distinct; requested runtime failure is nonzero.
- Run the explicit SDK `doctor --dest ABS_RUNTIME` from the retained verified native-tools copy. The workspace helper neither creates nor removes that environment.
- Check the runtime handoff to the intended new Cursor process. A shell variable or successful CLI doctor does not prove the GUI inherited it. Do not launch/reload a normal profile to make a support check pass.
- If hooks or local imports are disabled/untrusted/managed, record unavailable/not observed. Do not weaken trust, policy or ownership checks. Fresh profile/user-data directories do not isolate all OS-home hook sources.

GuardTrellis status reports omit matched values, but health/plan output can contain local paths. Cursor's native hook debug logs can contain raw event metadata or input. Do not attach those logs or a transcript wholesale. Review any proposed screenshot carefully; crop account, workspace and conversation information. Do not provide an unredacted screenshot merely because it is easier than copying metadata.

## Common outcomes

| Outcome | Safe next step |
| --- | --- |
| Outer/native hash, manifest or allowlist mismatch | Stop before executing/installing; confirm the intended artifact and trusted checksum with the issuer. Do not repair or relabel the unknown ZIP |
| Existing control or repeat install refused | Inspect existing health/ownership; use reviewed removal/reinstall. Do not overwrite it or create a duplicate hook |
| Linked, moved, modified or unknown owned state | Preserve files for local inspection; use the matching bundle. Do not edit the ledger, bypass refusal or broaden deletion |
| Concurrent configuration change / partial install | Keep the reported incomplete state and unrelated changes. Inspect locally; there is no force cleanup or universal filesystem compare-and-swap guarantee |
| Runtime setup incomplete or doctor unavailable | Confirm trusted Python, uv, exact SDK/source pin, fresh external destination and dependency/cache access. Never fetch dependencies during prompt handling |
| Config ready, runtime unavailable | The binding may be intact while local checking is unavailable. Do not label it active protection; use explicit runtime repair/replacement scope |
| CLI ready, Cursor not observed | Check only the separately approved isolated activation procedure. Native command/output/load evidence is required; SDK tests alone do not prove IDE behavior |
| Email/phone echoed by ordinary chat | That path does not redact. Use Terminal `prepare`, inspect masked stdout, and treat later `--open`/Cancel as a separate editor action |
| Source removed while a native window still shows a plugin | Close the entire owned process; verify a fresh approved instance. Saving/deleting config is not a reliable live unload |
| Runtime removal refused | Keep its ownership record and changed files; confirm it is unused and inspect. Never delete shared environments or profiles |

## Manually reviewed metadata template

There is no automatic collector, telemetry export or upload command. Fill this template yourself, remove unnecessary fields and review the entire message before sending through a confirmed private route. Use `<workspace>`, `<bundle>`, `<runtime>` and `<native-tools>` instead of personal paths. Share only information needed for the specific request.

```text
Artifact:
  Outer bundle filename/version:
  Outer SHA-256 and trusted checksum source description (no credentials):
  Inner native SHA-256:
  Helper/bootstrap SHA-256:

Environment:
  Cursor build/commit and OS/architecture:
  Python / uv / SDK versions:
  Isolated or normal context: (do not change it for this report)

Step and result:
  plan / install / health / explicit runtime doctor / remove:
  Exit code:
  Static status / reason code / finding codes only:
  Configuration state:
  Runtime local state:
  Native loading/unload: observed / not observed, with boundary named:
  GUI runtime consumption: observed / not observed:

Minimal synthetic reproduction:
  Command shape with placeholder paths:
  Fictional input only, if needed:
  Expected result:
  Actual metadata result (no matched text):
  Any unrelated configuration preserved? yes / no / unknown

Authorization for any next test:
  Read-only/offline only, or explicitly named isolated host action:
  No prompt/provider/model usage unless separately approved:
```

Do not send raw prompts, source code, matched secrets/PII, Hook Input/Output dumps, native debug logs, provider transcripts, account/user emails, session/conversation IDs, environment dumps, tokens, OAuth data or credentials. A checker report's input-free design does not sanitize unrelated files or logs. Do not reproduce with real data simply to increase confidence.

Email or other voluntary support correspondence goes to the recipient and communications providers used for that exchange. No blanket no-retention or zero-network promise applies. Review the current privacy terms before contacting support. A manually supplied support request does not authorize outreach to others, new telemetry, a hosted service or changes to normal profiles, authentication or managed policy.
