# Public evidence and limitations

## Local service and incident-policy refresh — 30 October 2026

Service terms, publisher support/incident responsibilities and support-data handling are prepared locally for native/helper **0.1.0-preview.4 / SDK 0.1.9**. Root [TERMS.md](TERMS.md) and [SECURITY.md](SECURITY.md) link to complete policies shipped inside both native/helper SUPPORT.md files; native PRIVACY.md covers local data flow. The Apache license, notices, runtime marker, SDK locks, hook/plugin configuration and executable logic are unchanged. This documentation-only source update has local validation. No current-source GitHub CI, reindex result, download release, marketplace approval or listing is claimed. Application-time source was 1ebfd6a, followed by the README-only public update c66b16e; those earlier snapshots do not include these policies. CI 40936455108 remains bound to 1ebfd6a.

| Locally verified artifact | SHA-256 |
| --- | --- |
| Native advisory 0.1.0-preview.4 | `1dd58f7d6d165db44708608f608691c4945a4ef719dd6ffafe6f7a500bcb691b` |
| Complete helper 0.1.0-preview.4 | `0bdf1726eabdc36e6f3ed270d9a5c18bd13887c9e330aa4be06895c07d64a82a` |

Native/helper archives each build twice with identical bytes and pass strict verification. Local checks cover all four phases: **146 tests / zero skips**, locked Ruff/format/strict mypy/shell checks, artifacts and unopened SDK/helper lifecycle. Environment: macOS 27.0.1 arm64, Python 3.12.1, uv 0.8.17. Earlier bootstrap attempts failed; static/lifecycle were then verified separately with a copied retained SDK 0.1.9 cache. The failed attempts are retained; this is aggregate phase validation, not a claim that the initial all-phase command passed. UV offline mode was enforced and Python downloads were disabled; no dependency download, IDE activation or provider call occurred.

Relative to the previously published-source candidate at c66b16e, native changes are README, PRIVACY, SUPPORT and the derived SOURCE-MANIFEST; all other 19 members are exact. Relative to accepted native `a655171e…ad45f`, all **17 implementation/configuration members** remain exact; the six documentation/manifest differences are the same categories recorded below. The helper builder changes only its declarative embedded-native checksum; installer/bootstrap/ownership logic is unchanged. The new whole ZIPs have **not** been run in Cursor, and no submitted-prompt, trust, failure/bypass, downstream, marketplace-lifecycle or additional-platform claim is added. Codex discovery remains pending and MCP remains deferred.

The dated reports below retain their original wording, versions and checksums as historical snapshots. Their earlier “current candidate” headings and validation outcomes do not relabel this new local policy revision or authorize publication. Use the hashes above for the current local source build.

## Historical dated evidence — preserved

Source-preview evidence — 29 October 2026. This sanitized summary does not reproduce private trial records or certify a marketplace listing.

## Current candidate

Native/helper **0.1.0-preview.3**, SDK **0.1.9**, is a local notice/documentation/package revision. Preview.3 has not been tested in a real Cursor host. Helper/bootstrap/runtime/hook implementations, SDK/policy defaults and runtime tag `0.1.0-preview.1-sdk0.1.9` remain unchanged; newly packaged bytes require their own immutable hashes and affected validation. The checksums below identify the locally verified artifacts; no release download is published. A later release must bind the exact source revision, package and checksum.

## Offline preview.3 verification

One full four-phase run passed on **macOS 27.0.1 / arm64, Python 3.12.0, uv 0.8.17**, using the frozen 71-file native-only source copy and a copied offline cache. No IDE or provider was contacted.

- **130 tests passed, zero skips.** Native builder/runner/launcher/runtime/workspace/delivery/public-copy suites were discovered; no legacy skills or service tree was needed.
- Locked tooling setup, Ruff 0.16.9 lint/format, mypy 2.3.1 strict typing and shell syntax passed. Canonical advisory source/catalog verification and two matching strict builds per native profile passed.
- Real SDK **0.1.9** setup, doctor and removal passed in an owned external temporary runtime. Native and complete-helper plan/install/health/remove ran only in unopened owned workspace fixtures and preserved unrelated hook configuration and runtime metadata.
- Local clean/advisory and synthetic-secret/enforcing invocation checks passed; email/phone preparation produced masked stdout. These were local process invocations, not IDE events; no prefill, Send or downstream provider observation occurred.
- Moving the extracted source preserved doctor behavior and source hashes. Owned runtime removal verified absence. The complete advisory helper reproduced and strictly verified twice with the exact embedded native pin.

| Artifact | SHA-256 |
| --- | --- |
| Advisory native | `0ad5fba2da3f2762fe7f8f3c4bb1ae60a6a795966f08f7fd98c8c8afe442a27f` |
| Explicit enforcing private-acceptance variant | `fc2418c1b6dd0c27a4cfca0235a78f46f3da71415b74e68fa4c4fe361d4096c2` |
| Complete advisory helper | `29a8d410b19248090f8efd5585bcba859470c8a03f0fb3e97473254e3b2b8d5b` |

These package bytes match the earlier local preview.3 freeze. Public-root documentation was then updated to record source availability and these observed results; those three root files are outside native/helper archive inputs. Source availability is separate from downloadable releases, live CI, host acceptance and marketplace review. The commit-bound CI result below is now observed; the workflow remains manual-dispatch only.

## Commit-bound GitHub CI

[Manual run 40880665999](https://github.com/sahilmathur254/guardtrellis-cursor/actions/runs/40880665999) passed at exact source commit [`832fb5e3b5ddc5dc5af32f9fc5f9c9a67da8e75f`](https://github.com/sahilmathur254/guardtrellis-cursor/commit/832fb5e3b5ddc5dc5af32f9fc5f9c9a67da8e75f), attempt 1, on 29 October 2026. All four verification phases and all 13 job steps succeeded, with **130 tests and zero skips**.

The standard hosted runner was **macOS 26.6.2 / build 25G83, arm64**, image `macos-26-arm64` version `20261013.0424.1`, using **Python 3.12.10 / uv 0.8.17**. This is separate from the local environment above. Locked static checks, canonical/reproducible native artifacts, actual SDK **0.1.9** setup/doctor/removal and native/complete-helper lifecycle in unopened workspace fixtures passed. Native/helper hashes and the embedded advisory pin match the preview.3 table above; tracked-source preservation passed.

The run used a standard public-repository runner. Its timing receipt reports **0 billable macOS milliseconds**, with no uploaded artifact or persistent cache. Package builds were verified in disposable roots; no release download was published. CI performed ordinary Action/package downloads but no IDE activation, prefill, Send, provider request or downstream observation.

One nonblocking warning reported that the pinned checkout action targets Node 20 and was forced to run on Node 24. Checkout, all phases and cleanup succeeded; the pin was not changed as part of this evidence refresh. A later supported immutable-pin update needs its own review and checks.

This receipt applies to the named source commit. The evidence-page refresh is outside native/helper archive inputs and does not change SDK/runtime/policy or package hashes. Hosted process/fixture checks do not establish native Cursor prompt enforcement, stable trust, default-opener behavior or a wider platform/Python matrix.

## Bounded prior preview.2 observations

On Cursor **3.27.22 / macOS arm64**, exact preview.2 no-prompt open/restart loaded one plugin with zero failures. Fresh open after recognized helper removal showed zero loaded/retained plugins and zero failures. Local SDK readiness and main-process runtime binding were observed; native prompt-hook SDK consumption was not.

Separate component/version/four-command/one-advisory-hook UI and masked email/phone review → Cancel were observed in a named profile sharing application/account state. The preparation function used an explicit-profile CLI launcher callback. Create Chat/Send was not invoked and an empty draft was preserved. This does not certify the bundled default `/usr/bin/open -a` opener or fully separate account/user-data isolation.

Trust remains inconclusive. Two fresh owned user-data cases initially reported project hooks disabled in an untrusted workspace, then later ran bootstrap. Effective trust at the later event and transition cause were not established. No continuous suppression, trusted/untrusted enforcement or bypass finding is claimed.

Frozen prior advisory native: `10710d54fce7e6cda8101bbe81753aabe69aa7234b4b0f6676bca3c8f29e34db`. Frozen prior complete helper: `d2ec07cce5365586a6be471b5afba90b54f4b3f3205b8900af72615ff087b922`. These identify prior preview.2 artifacts, not current downloads or preview.3. Keep prior versioned bytes and dated evidence intact.

## Unverified boundaries

Native submitted-prompt SDK/cwd/decisions, disabled/failure/timeout/ordering/bypass/downstream behavior, stable trust, default opener and ordinary marketplace installation remain unverified. Historical preview.1 or SDK 0.1.6 trials do not fill these gaps. No full background-egress or account-wide billing audit is claimed.

A scanner finding, a requested cancellation, cancellation UI and a measured blocked downstream request are different observations. The default advisory profile requests continuation. Terminal masking is a separate reviewed workflow, not automatic prompt rewriting. Names and unsupported contact formats can remain. Attachments/history/indexing/file reads/shell/MCP/inline completion/other agents are outside coverage; native Windows/Linux is not advertised.

Offline source/test/artifact checks, local SDK lifecycle, actual native acceptance, live CI, public source, downloadable release, vendor review and marketplace publication remain separate evidence states. Do not infer one from another. Current validation results must be tied to the exact accepted source/artifacts; a saved workflow is not a completed GitHub Actions run.


## Local preview.4 preparation — 29 October 2026

The preceding preview.3 source/CI snapshot is preserved verbatim, including its then-current host limits. New **0.1.0-preview.4 / SDK 0.1.9** is a local explicit-target prefill candidate, not a new commit, CI run, release download or listing. Runtime tag `0.1.0-preview.1-sdk0.1.9`, hook policy and scanners stay independent of package version. Record new package checksums and actual local check results separately; no new pass count is asserted here.

The product command now requires `--open --user-data-dir ABS --extensions-dir ABS --cursor-profile NAME`, using the fixed installed desktop CLI instead of an unscoped system opener. Accepted checked text alone enters the prompt deeplink; local stdout preparation remains available. [Official deeplinks](https://cursor.com/docs/reference/deeplinks) require user review and do not automatically execute prompts. The shipped Cursor 3.27.22 `--open-url` route is named-build compatibility, not a guarantee across Cursor versions or of an exact destination workspace/window. Review and Cancel on a wrong target. A timeout/nonzero result may follow a handoff; there is no automatic retry or fallback.

Separate exact preview.3 observations on Cursor 3.27.22/macOS arm64 covered loading, four guides/one advisory hook, local SDK readiness, cold reopen, an explicit-profile callback's masked review with owner-assisted Cancel, and fresh-session removal. Native prompt decisions/failures/bypasses/downstream, stable trust and ordinary marketplace lifecycle remained unverified. **Preview.4 has not been tested in a real Cursor host**; its changed product launch path needs its own isolated native review/Cancel acceptance. Neither prior callback results nor the older CI run fill that gap. No Send/provider/model workflow, publication or marketplace submission is part of this local revision.


## Accepted preview.4 runtime and documentation refresh — 29 October 2026

All preceding sections are dated source/CI/pre-trial snapshots retained verbatim. This section supersedes their earlier statements that preview.4 had not been observed in a real host. It does not reassign the earlier CI run or erase its limits.

The accepted **0.1.0-preview.4 / SDK 0.1.9** advisory native archive SHA is `a655171ed0ef3416baa0553d6afac9fd0f3954c1cfdfdea4f0b5502a800ad45f`; the accepted complete helper SHA is `63fc0224a78cd63fdb1f97ae965d21ea706ceb427ba65f5d6624f0fae5f3df25`. On **Cursor 3.27.22 / macOS 27.0.1 arm64, Python 3.12.0**, native loading was confirmed before the actual installed shell `prepare --open` command with the full user-data/extensions/profile tuple. The intended isolated window showed the synthetic email/phone draft masked to `[PII]`; automated Escape removed the review and preserved an empty draft. No launcher callback or monkeypatch was used. Fresh cold reopen showed **1 loaded / 0 retained / 0 failures**, and fresh open after owned removal showed **0 loaded / 0 retained / 0 failures**. Owned source/runtime cleanup and preservation of unrelated fixture configuration were verified. No Create Chat, Send or provider/model workflow was initiated.

The accepted implementation's prior offline run passed **146 tests / zero skips and all four phases**, including locked static checks, strict reproducible artifacts and real SDK/helper lifecycle in unopened fixtures. This is local evidence; GitHub CI above remains bound to 832fb5e and its 130-test result. It does not cover new uncommitted source.

This documentation-only refresh corrects public/native/helper evidence descriptions while retaining the accepted executable, SDK/lock, launcher, hook configuration and runtime identities. New documentation creates new package checksums and a regenerated source manifest/pin. The corrected ZIPs are **not themselves whole-package host-tested**: named-host behavior traces to the accepted runtime bytes above, with an exact unchanged-implementation inventory and affected local checks recorded separately before delivery. Do not relabel a new archive hash as directly observed in the host or embed a helper's own current checksum in a file selected by that helper archive.

Trust remains inconclusive: an initial untrusted workspace suppressed project hooks, later enabled them without a correlated effective transition, and a cold reopen loaded the plugin. Cold process shutdown included forced owned termination after grace; it is not graceful GUI Quit or immediate live unload. The normal Cursor window was owner-closed during foreground assistance, so concurrent normal-instance routing was not established. Separate storage does not provide hermetic HOME/OS isolation. On macOS, choose a short canonical user-data path: IPC socket path limits can reject an otherwise valid directory before workspace loading. Directory validation alone does not guarantee that the host socket path fits.

Native beforeSubmitPrompt SDK/cwd/decisions, stable trust/disabled behavior, failures/timeouts/malformed output/ordering/bypasses, downstream suppression, ordinary marketplace lifecycle and native Windows/Linux remain unverified. The advisory hook requests continuation; ordinary chat is not rewritten. This review/Cancel evidence establishes neither secret enforcement nor complete egress suppression. No public release, form submission, vendor approval or marketplace listing follows from this summary.


## Final local copy-refresh checks and first-listing scope — 29 October 2026

The first listing is an **experimental macOS reviewed-prefill preview**: selected email/phone masking and recognized-secret withholding during local preparation, followed by explicit native review. The included advisory hook is native-submission-unverified and requests continuation; no enforcement, automatic ordinary-chat rewriting or full egress guarantee is advertised.

The copy-refresh advisory SHA is `092f10ac145838ffc25f11396b129b808bc5ed1f782cd9cb89da3c04758ae064`; complete helper SHA `488a963c21a62d8e7d45797eedd5eb3d344c538ba4a066c7e126ef63010df1eb`. Both native profiles/helper build reproducibly and strictly verify. **146 tests / zero skips and all four offline phases passed** on macOS 27.0.1 arm64/Python 3.12.0/uv 0.8.17, including locked checks and actual SDK 0.1.9/helper lifecycle. This is not a new CI or IDE run. Root README/reviewer/publisher SVG additions are outside native/helper archive inputs and received separate local disclosure/link/syntax/artwork review.

Relative to accepted native `a655171e…ad45f`, the changed native members are README, COMPATIBILITY, PRIVACY, SUPPORT, the prepare command guide and derived SOURCE-MANIFEST. All 17 other members, including the plugin/hook manifests, native icon, launcher, preparer, scanners, runtime setup and SDK locks, are byte-identical. The helper's changed source pin is declarative; its ownership/bootstrap/installer logic is unchanged. The new whole archive hashes were not themselves run in the IDE; the accepted named-host implementation result maps through this exact equality. Do not relabel them as new whole-package host acceptance.

Publisher identity/contact and reviewed-prefill scope were confirmed by the owner for this local packet. Preferred `@guardtrellis` availability is untested; no form entry, terms acceptance, submission, release or public push was performed. The existing native icon remains unchanged; separate publisher artwork embeds the supplied PNG bytes exactly on a white SVG plate, with no scripts/external loads. A future approved source commit must be bound to checks and verified public logo/source URLs before application.
