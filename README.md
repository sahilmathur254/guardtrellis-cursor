# GuardTrellis for Cursor

Experimental source preview. Not listed in the Cursor Marketplace; no release download is published.

Experimental macOS reviewed-prefill preview using the public GuardTrellis SDK **0.1.9**. Explicit Terminal preparation masks selected email and contiguous international-phone shapes and withholds recognized secret patterns or unavailable checks before opening a reviewed draft. It never presses Send; ordinary chat is not automatically rewritten. The included advisory prompt hook requests continuation and remains unverified in native submitted-prompt use; no enforcement or complete-egress claim is made.

Native/helper identity **0.1.0-preview.4** adds explicit-target reviewed prefill. Its accepted runtime was verified on Cursor **3.27.22 / macOS 27.0.1 arm64, Python 3.12.0**: plugin loading preceded the actual installed shell command, native email/phone masking review, automated Escape to an empty draft, cold reopen and owned removal. This local documentation refresh corrects earlier pre-trial copy and creates new package checksums; it is not a new whole-package host trial. [Current evidence and exact runtime mapping](PUBLIC-EVIDENCE.md#accepted-preview4-runtime-and-documentation-refresh--29-october-2026) identifies the tested archives and remaining limits. Native submitted-prompt behavior, stable trust, failures/bypasses/downstream and ordinary marketplace installation remain unverified. Attachments, history, indexing, file/shell/MCP activity, inline completion and other agents are outside the prompt boundary. Native Windows/Linux and complete prompt-egress prevention are not advertised.

Terminal `prepare` still emits selected email/phone masking without opening an editor. A deliberate later `prepare --open` now requires all three target options: `--user-data-dir`, `--extensions-dir` and `--cursor-profile`. It uses the fixed installed desktop CLI, with no system-opener/default-profile fallback. Only accepted checked text is passed to the local review. The target is requested, not a guarantee of the precise workspace/window: review it and Cancel on a wrong destination. A timeout/error can occur after handoff; inspect the instance before any manual retry. See the [workflow](integrations/cursor/plugin/README.md#request-a-reviewed-draft-in-an-explicit-target).

On macOS, choose a short canonical user-data path: IPC socket path limits can reject an otherwise valid directory before workspace loading. Directory validation alone does not guarantee that the host socket path fits.

Use the complete matching helper bundle and an independently trusted checksum for deliberate installation into an unopened selected workspace. The native ZIP alone does not include the installer. Follow the [complete helper guide](integrations/cursor/delivery/README.md), [native compatibility](plugins/guardtrellis-cursor/COMPATIBILITY.md), [privacy](plugins/guardtrellis-cursor/PRIVACY.md) and [support](plugins/guardtrellis-cursor/SUPPORT.md). Source availability and extraction do not activate hooks. Initial explicit setup can contact package registries; prompt handling never installs a runtime.

This repository maintains the Cursor-specific templates, helpers, packaging, documentation and tests. The public SDK remains independently useful and owns scanner implementations. No hosted scanner, account system, MCP service or enterprise layer is included. Historical `adapters/codex/redact_prompt.py` and runtime-config names are retained compatibility paths for shared local preparation, not a Codex host integration.

The declared Python range is 3.11–3.14; named local/host evidence used Python 3.12. The runtime marker intentionally remains `0.1.0-preview.1-sdk0.1.9`, independently of package version. A matching tag does not authorize reuse/removal of an unknown environment. Keep retained verified tools for removal after project source deletion.

[Maintenance](MAINTAINING.md) describes authoritative/generated ownership and checks. A source repository, downloadable release and marketplace listing are separate milestones. Any later download needs an approved immutable identity and trusted checksum; no marketplace approval or universal installation route is claimed.

Support is voluntary and manually reviewed metadata-only, without automatic collection/export or SLA. Do not send raw prompts, source, matched values, credentials or host logs. Host/provider handling remains separate. [License](LICENSE) · [Notices](NOTICE).

## Publisher and review

Publisher: **GuardTrellis**, maintained by **Sahil Mathur** as an individual. Preferred publisher handle `@guardtrellis` is not reserved or availability-tested. Monitored public support/security contact: [sahil.mathur2504@gmail.com](mailto:sahil.mathur2504@gmail.com); manual handling, no response-time SLA or enterprise offer. See the [reviewer guide](REVIEWER.md) for the tested local workflow and a synthetic review/Cancel checklist.

The [publisher artwork](assets/publisher-logo.svg) uses the owner-supplied shield/checkmark image unchanged on a square white SVG background plate; it is separate from the frozen native plugin icon. The image file is local source until an approved public push; no form URL, namespace reservation, marketplace application or vendor approval is implied. Existing older website/tester downloads keep their own version scope.
