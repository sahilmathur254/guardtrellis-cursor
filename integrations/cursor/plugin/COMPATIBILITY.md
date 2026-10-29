# Native Cursor compatibility and evidence

Candidate: `guardtrellis-cursor` **0.1.0-preview.4**, SDK **0.1.9**, **advisory by default**. This native source has one command hook, four command guides, SDK runtime source/lock metadata and native-specific privacy/support. It has no portable/Codex/Claude manifest, integration skill, MCP configuration, interpreter or virtual environment. The complete helper delivery, older adapter tester kit and OpenAI skills packages are distinct artifacts.

## Version and evidence matrix

| Surface | Current boundary |
| --- | --- |
| Accepted preview.4 runtime | Actual installed shell/full-target review after plugin loading, masked email/phone draft, automated Escape/empty input, cold reopen 1/0/0 and fresh removal 0/0/0 on Cursor 3.27.22/macOS 27.0.1 arm64/Python 3.12.0; no Create Chat/Send/provider workflow |
| Documentation refresh | New checksums; unchanged executable/configuration/runtime mapping to accepted preview.4; new archive is not itself whole-package host-tested |
| Prior preview.3 bounded host checkpoint | Exact loading, four guides/one advisory hook, local SDK readiness, cold reopen and fresh removal observed on Cursor 3.27.22/macOS arm64; native prompt SDK consumption not observed |
| Prior preview.3 reviewed prefill | Actual installed SDK/preparer with explicit-profile CLI callback; masked review observed, owner-assisted Cancel independently verified, no Create Chat/Send; callback result does not certify preview.4's product command |
| Prior preview.2 and preview.1 | Historical lifecycle/component/review evidence; does not substitute for new-package acceptance |
| Runtime/hook implementation | SDK 0.1.9 checker/setup and hook policy retained; no scanner, policy or runtime migration from the prefill-route revision |
| Runtime marker/default identity | `0.1.0-preview.1-sdk0.1.9`, intentionally unchanged and independent of native/delivery version |
| Python/tool evidence | Prior named Python 3.12.0 / uv 0.8.17; declared Python 3.11–3.14 is not a tested native matrix |
| Initial target | macOS arm64 Cursor desktop; other builds, macOS architectures, Windows/Linux, cloud/remote hosts and other agents are not advertised |
| Native prompt behavior | Actual beforeSubmitPrompt invocation, root/cwd/runtime consumption, advisory/enforcing outcome, timing and downstream requests remain unverified for preview.4 |
| Trust/failure/lifecycle breadth | Stable effective trust/disabled-state behavior, ordering, failures/timeouts/malformed output, bypasses and ordinary marketplace lifecycle remain unverified; earlier trust transition was inconclusive |
| Explicit-target prefill | Required user-data/extensions/profile options; fixed installed desktop CLI and minimal environment; no unscoped OS fallback. Shipped 3.27.22 recognizes --open-url, not a general version or exact workspace/window routing guarantee |


Retaining the runtime tag avoids silently redirecting a working default environment. It is not proof an existing runtime is suitable or safe to share/delete. Setup still requires a fresh destination; explicit doctor validates the intended owned record/source. A matching SDK string alone is insufficient.

On macOS, choose a short canonical user-data path: IPC socket path limits can reject an otherwise valid directory before workspace loading. Directory validation alone does not guarantee that the host socket path fits.

## Scanner and preparation contract

The prompt hook checks only `beforeSubmitPrompt.prompt`: at most 65,536 input-event bytes and 10,000 Python characters. It recognizes selected GitHub classic/fine-grained, AWS access-key-ID and PEM-private-key shapes. It does not validate credentials or detect every secret; benign examples may produce findings. In the advisory package a finding/unavailable check requests continuation. The separate enforcing artifact is not this default and needs its own reviewed opt-in and native evidence.

The prompt hook does not rewrite prompts. Ordinary PII checks/redaction are off. Explicit Terminal preparation applies secret signatures first, withholds recognized secrets/errors/unavailable input, then masks selected email and contiguous international-phone shapes to `[PII]`. Names and unsupported shapes can remain. Only explicit `--open` requests a reviewed unsent draft; it is a separate editor action. The accepted runtime’s named-host review/automated Escape is observed; new documentation-only archive bytes require their own hash/mapping and affected checks. Slash commands are agent guidance, not a pre-provider local editor boundary.

Attachments, history, indexing, file reads, shell/tool/MCP calls, inline completion, Cmd+K and other agents are outside coverage. GuardTrellis diagnostics omit content, but Cursor's own logs/history and provider handling are separate. Cursor may use text for naming before this prompt boundary. A finding, requested decision and observed downstream block must not be conflated; no full egress/network suppression follows from local checks.

## Historical observations and delivery

Earlier SDK 0.1.6 adapter trials observed selected cancellation UI on Cursor 3.24.18/macOS arm64 and reviewed prefill/Cancel/editable unsent drafts on 3.24.18/3.27.22. These are different source/runtime/package identities; they do not certify preview.4 or Windows support.

The complete workspace helper stages one project lifecycle entry and fixed owned source. It references an external SDK environment without installing/deleting it. Local doctor/health are separate from GUI trust/loading/execution. Use a retained verified native-tools copy for runtime removal after helper removal; closing the owned process and a later authorized fresh-open observation are distinct from deleting configuration.

See [README](README.md), [privacy](PRIVACY.md) and [support](SUPPORT.md). A new immutable hash and source map are required for each candidate. Public-source disclosure, support/policy approval, installed workflow acceptance, marketplace review and publication remain separate; this document is not a support certification.
