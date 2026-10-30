# Maintaining the Cursor source

This repository maintains the Cursor-specific templates, helpers, packaging, docs, tests and CI. The public GuardTrellis SDK independently owns the checking engine. The initial source transfer preserves the selected donor bytes and separately reviewed public-root copy, without importing donor Git history. No automatic synchronization with the companion is provided. Review shared-source backports explicitly.

## Source and generated ownership

Preserve the selected relative layout. `integrations/cursor/plugin/` plus the explicit shared adapter/runtime inputs in `scripts/cursor_release.py` are authoritative. `plugins/guardtrellis-cursor/` is generated advisory source with `SOURCE-MANIFEST.json`; `.cursor-plugin/marketplace.json` points only there. Do not edit generated implementation files. `check-export` detects exact drift read-only; fresh export refuses an existing target. Apply reviewed generated deltas without reset/stash/clean or broad deletion.

The native and outer builders select the same native-specific `integrations/cursor/plugin/NOTICE`. SDK licenses/notices remain separate; excluded legacy skills/evaluation datasets are not native dependencies and must not be imported to satisfy old notices. Companion cross-family regressions remain private and separate from the destination's native-only public-copy suite.

Root README, public evidence, maintenance and NOTICE describe this Cursor-only source. The existing Apache LICENSE bytes and attribution are retained. The companion root README/NOTICE and private planning tree are not part of this source. Do not import excluded data or private history when maintaining shared code.

## Validation and candidate identity

From the reviewed source root, using trusted Python 3.12 and uv 0.8.17:

```sh
python3 -I -B scripts/cursor_release.py check-export --source .
python3 -I -B scripts/check_cursor_release.py --phase all
```

The four phases cover native-only tests, locked static checks, reproducible/strictly verified artifacts and exact-extraction SDK lifecycle in unopened owned fixtures. Fail on empty discovery or skips. Build both native profiles and complete advisory helper twice, compare exact bytes/manifests/pin, and preserve old artifacts. Local validation does not launch Cursor or call a model/provider. Dependency setup may use package registries unless a complete copied cache and `UV_OFFLINE=1` are supplied; no Python download is permitted.

CI is **manual-dispatch only** with pinned Actions/tool versions, read-only permissions and macOS/Python 3.12 scope. Obtain separate run/usage approval before dispatch. Adding automatic push/PR triggers is a later explicit decision; saved definitions/local results are not live CI evidence or a native Windows/Linux claim.

The native/helper package is `0.1.0-preview.4`; SDK stays `0.1.9` and runtime identity stays `0.1.0-preview.1-sdk0.1.9`. The explicit-target prefill change creates new native/helper hashes and inner pin; it does not migrate a runtime or certify native behavior. Historical preview.3 CI remains bound to 832fb5e; do not relabel that run as preview.4 validation. Historical codex paths/metadata are compatibility identifiers, not a transferred host integration. Keep ownership/removal refusals and retained tools; never delete an environment merely because the tag/SDK matches.

## Reviewed prefill compatibility

`prepare` without options is local stdout preparation. `prepare --open --user-data-dir ABS --extensions-dir ABS --cursor-profile NAME` requires the complete explicit target; partial/unknown arguments and unsafe directories are refused. Keep canonical existing user-data/extensions directories distinct, nonoverlapping and outside normal IDE roots. The fixed installed macOS desktop CLI receives the selected directories/profile and only a checked prompt deeplink. There is no PATH-discovered CLI, agent command, OS-opener fallback or automatic retry. The minimal environment omits inherited IPC/remote/portable/development routing and Node overrides; do not restore them casually.

[Cursor documents prompt deeplinks](https://cursor.com/docs/reference/deeplinks) as reviewed prefill with a 10,000-character encoded-URL limit. The shipped Cursor 3.27.22 CLI recognizes `--open-url`; it is not a general cross-version routing guarantee. The explicit target is a request; no exact workspace/window guarantee follows from argv or a zero exit code. The accepted preview.4 runtime (a655171ed0ef3416baa0553d6afac9fd0f3954c1cfdfdea4f0b5502a800ad45f) was observed through the actual installed product command after native loading, with masked review and automated Escape/empty draft. Earlier callback evidence remains historical. Documentation-only artifact refreshes need an exact unchanged-implementation mapping and affected checks; their new archive hashes are not whole-package host-tested by association. Any changed executable/configuration path needs its own affected native acceptance. A failed/timeout handoff may already have opened review; never automatically retry or fall back. No Send/provider scope follows from prefill acceptance.

On macOS, choose a short canonical user-data path: IPC socket path limits can reject an otherwise valid directory before workspace loading. Directory validation alone does not guarantee that the host socket path fits.

## Transfer, disclosure and recovery

Import reviewed licensed file bytes with exact hashes/modes, not private Git ancestry, environments, operational records or raw host logs. Before changing public refs, inspect the branch, status, relevant diff and applicable AGENTS guidance. Preserve existing user changes and reconcile concurrent edits. Keep the owner-created initial root commit in ancestry; do not reset or force-push over it.

Any public branch push discloses source even if CI is manual-only. Obtain exact file/ref/disclosure and commit/push approval first. Live CI usage, host activation/prompt scope, download deployment, publisher terms/review and Publish are separate gates. Keep experimental [evidence limits](PUBLIC-EVIDENCE.md); no automatic-other-agent interception or enterprise-readiness claim.

Before remote writes, recovery means retaining/discarding only owned local staging and preserving donor/destination/old artifacts. Later approved public corrections use reviewed forward fixes/reverts, not history erasure. Installed rollback follows the matching owned close/remove/reinstall guide; no broad cleanup, shared-runtime deletion or normal-profile changes.

## Native service and incident documentation

Root [TERMS.md](TERMS.md) and [SECURITY.md](SECURITY.md) are repository entrypoints. Complete service terms, support-data handling and the owner incident procedure ship in both maintained native/helper SUPPORT.md files; native PRIVACY.md describes full local data flow. Keep these policies synchronized without importing older website/skill terms. They do not alter Apache/third-party rights, promise a response-time SLA or waive accepted Marketplace duties.

The owner manually triages reports and promptly provides required incident notice to legal@cursor.com; security-reports@cursor.com is Cursor's separate technical reporting route. Follow the packaged procedure, minimize shared data, preserve unrelated/owned state and verify only the recovery actually observed. Actual communications, source/reindex/release changes and host/provider actions still need their concrete authorization; documentation does not send or activate anything.

A documentation-only policy refresh changes SOURCE-MANIFEST/native/helper hashes and the declarative embedded-native checksum. Keep old artifacts and CI/host evidence immutable; prove executable/hook/runtime/SDK-lock equality and verify reproducible new archives. New hashes are not a new whole-package native trial or current-source GitHub CI.
