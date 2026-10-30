# Support for the experimental Cursor helper bundle

Publisher and operating support/security/privacy owner: **Sahil Mathur**, [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com). Support is manual, with no fixed response-time SLA. The service terms and incident procedure below cover this complete helper and its matching native preview; older website distributions are separate.

Use the publisher email above for private support/security/privacy reports. Older website support/privacy pages describe separate distributions and are not the current native policy. This bundle carries service terms, support-data handling and incident guidance below; the embedded native archive carries its full PRIVACY.md. Do not post sensitive vulnerability details in public issues or assume a private GitHub advisory intake exists. The tools do not open tickets, send email or upload diagnostics automatically.

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

## Service terms

Prepared 30 October 2026 for GuardTrellis for Cursor native/helper **0.1.0-preview.4 / SDK 0.1.9**. Publisher and support owner: **Sahil Mathur**, [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com). These terms describe this local integration and its publisher support. They do not govern the independently useful SDK, older website downloads or other host integrations. Cursor and other providers supply their own services under their own terms.

The preview is provided without a GuardTrellis usage fee or account. It is an experimental macOS reviewed-prefill workflow: selected checks run locally, selected email/phone patterns are masked, and recognized secrets or unavailable checks withhold the prepared draft. You review any accepted draft and its destination/context before deciding to send. Names and unsupported forms can remain. Ordinary chat is not automatically rewritten. The included prompt hook is advisory; findings/errors request continuation, and native submitted-prompt behavior remains unverified. This is not complete PII/secret detection, an enforcement or egress guarantee, or an enterprise-managed service.

Software is supplied under the included [Apache 2.0 license](LICENSE), with attribution and third-party notices in [NOTICE](NOTICE). These service/support disclosures do not replace that license or narrow its copying, modification, redistribution or commercial-use permissions. Third-party license rights and attribution remain unchanged. The license's warranty and liability provisions apply to the extent permitted by law; mandatory rights are unaffected. No guarantee of uninterrupted availability, detection accuracy, a particular result or compatibility beyond recorded evidence is added here.

Use workspaces and data you are authorized to handle. Review source, trusted checksums, setup/removal instructions and the shipped privacy information before use. Keep credentials and unnecessary personal data out of demonstrations and support reports. The publisher does not acquire ownership of your content. Local preparation does not alter Cursor/provider terms, retention, permissions or network behavior; initial explicit dependency setup may contact package registries.

The publisher is responsible for technical support, maintenance and security handling, and will use commercially reasonable efforts to investigate reported issues and maintain a functioning, secure integration within its disclosed scope. Support is manual and has no fixed response-time SLA, around-the-clock staffing or emergency-response guarantee. Those limits do not waive accepted Marketplace maintenance, support or prompt incident-notification responsibilities. The [publisher incident procedure](#publisher-incident-procedure) applies to security reports.

You may stop using the integration and remove owned state with the matching verified tools. Close the affected owned process first; preserve unrelated configuration and shared runtimes. Do not force unknown ownership or assume removal erases host/provider history or backups. Updates require a reviewed source/version/checksum and the applicable vendor review route; a source change or marketplace delisting does not guarantee that existing installations update or stop running. Material documentation changes are dated, and earlier artifacts retain their own evidence and terms snapshot. No paid plan, automatic update or retroactive waiver is introduced.

Support-data categories, recipients, retention and request controls are described under [support data handling](#support-data-handling). No automatic collector or support upload is provided.

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

## Publisher incident procedure

Reports go privately to [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com), with a subject such as `GuardTrellis Cursor security report`. Start with reviewed version/hash/status metadata, a fictional reproduction, the suspected impact and what remains unknown. Do not include working credentials, private prompts/source or unrestricted host logs. Public issues are suitable only for non-sensitive bugs; do not assume a GitHub private-advisory intake has been enabled.

The operating owner follows this manual procedure:

1. **Receive and triage.** Restrict report access, record a minimal case identifier, affected artifact/version, facts, uncertainty and actions. Distinguish a documented limitation, support defect, vulnerability, data exposure or other incident. Prioritize active exposure and unsafe execution. Request only missing metadata; reproduce offline with synthetic inputs instead of real secrets, customer content or provider requests.
2. **Contain safely.** Identify the affected workflow/version and advise stopping that flow where appropriate. Prepare matching close/remove/rollback instructions while preserving ownership records, unrelated configuration and shared environments. If a real credential may have been exposed, its owner should use the issuer's approved revocation/rotation process; do not send the value to support. GuardTrellis has no remote kill switch, and delisting does not recall installed copies.
3. **Notify and coordinate.** Promptly notify **legal@cursor.com** of a security vulnerability, data breach or other security incident affecting the plugin or Plugin Data, as required by accepted [Marketplace Publisher Terms section 4.3](https://cursor.com/marketplace-publisher-terms). Do not wait for a complete investigation, a fix or the application decision before providing the required initial notice; distinguish known facts from suspected impact and follow up as facts change. Cursor also directs marketplace security reports to **security-reports@cursor.com** in its [security guidance](https://cursor.com/help/security-and-privacy/marketplace-security). Use that technical route as appropriate; it does not silently replace the contractual notice address. Share the minimum affected-version, impact, containment and contact facts needed, without raw prompts, matched values or credentials. Reporting or coordination is a deliberate owner action, never an automatic tool send.
4. **Fix and recover.** Prepare a scoped source correction or safe workaround, exact hashes, relevant regressions and affected native evidence where behavior changes. Obtain the applicable source/reindex/release approvals; do not assume a source push automatically updates marketplace users. Verify the recovery that was actually observed and record remaining limitations. Coordinate user notices and public advisories around actionable versions, mitigations and verified impact, without exposing customer material or unnecessary exploit detail. Coordination must not delay the required initial vendor notice.
5. **Close and minimize.** Record the resolution, affected/fixed versions, notifications and unresolved risks. Remove unnecessary attachments and working copies when their purpose ends; retain only the minimum case record needed for continuing support, security, vendor reporting or applicable obligations. Review retained records when the case closes and when those purposes end. Provider backups and third-party history have separate deletion limits.

The publisher remains responsible for this procedure. These documents do not send notifications or authorize an agent to contact anyone, alter accounts/profiles, rotate credentials, activate hooks, submit prompts, deploy or publish.

## Support data handling

Contacting support is optional. If you do, the publisher receives your sender/contact address, message, the reviewed metadata you supply and any unsolicited attachments. These are used to answer the request, investigate an issue, coordinate a fix and meet applicable support, security and reporting duties. Email and other communication providers handle delivery/storage under their own policies. No automatic exporter or telemetry collector sends this information.

The publisher may share only the minimum necessary case, version, impact and contact details with Cursor for marketplace/security coordination, and with advisers or authorities where needed for applicable obligations. Reports are not sold or used by the publisher to train models. An accidentally supplied secret or private payload should not be resent: access is restricted, unnecessary copies are removed, and only the minimum evidence needed for an incident or applicable obligation is retained. A synthetic replacement may be requested; complete raw reports are not routinely forwarded.

Retention is purpose-based, with no fixed retention period: review records at case closure and when continuing support/security/reporting purposes end, remove unnecessary attachments and working copies, and retain only what remains needed for those purposes or applicable obligations. Deletion from the publisher's active records cannot promise immediate erasure from provider backups, delivery systems, your own copies or Cursor/provider history.

Request access, correction or deletion through [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com), using minimal identifying information. The publisher will handle the request subject to applicable obligations and provider limitations; do not send credentials or identity documents as a test. No account system, automated deletion endpoint or universal no-retention/zero-network guarantee is offered.

## Helper privacy and local controls

The workspace helper reads the selected configuration/archive and its bounded ownership inventory. It stores local workspace/runtime/Python paths and source/configuration hashes in the owned record, plus the derived lifecycle entry in `.cursor/hooks.json`. It does not scan arbitrary files, collect a transcript or upload payloads. Health/plan output can reveal local paths; only an explicit runtime check executes local synthetic SDK probes.

Explicit SDK setup may fetch locked packages from registries, which receive request metadata under their own policies. Prompt processing never installs dependencies. Local source/runtime/records and any captured stdout, terminal scrollback/history, redirected files or test artifacts remain until their owners remove them. Close the owned process and use matching removal tools; workspace removal preserves the external runtime and unrelated configuration. Runtime removal is separate and refuses unknown/modified ownership. No remote recall or host/provider-history deletion is promised.

The embedded native archive contains its full `PRIVACY.md` alongside `SUPPORT.md`; after ordinary verified extraction, read those before activation or preparation. Accepted preparation can intentionally emit text to stdout or, on explicit reviewed prefill, a local Cursor CLI URI. OS/process tools, Cursor and providers have separate retention/network behavior. Cancel, local checking and removal do not prove zero egress or erase other copies. Names and unsupported personal-data formats can remain. No hosted scanner, publisher account system or automatic support collection is included.
