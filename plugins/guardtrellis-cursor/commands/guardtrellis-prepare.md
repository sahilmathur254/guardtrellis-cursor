---
name: guardtrellis-prepare
description: Explain Terminal email/phone preparation and a separate reviewed Cursor prefill request.
---

Explain the workflow only. Do not request private text in chat, read clipboard,
run commands, open Cursor or submit anything automatically. This command is agent
guidance; text pasted into chat has already reached the host and may reach a
provider. The prompt hook does not rewrite prompts; ordinary submissions are not
automatically masked. The hook is advisory by default.

Use only synthetic stdin in Terminal, with retained verified native-tools and the
explicit prepared SDK 0.1.9 runtime:

```sh
gt_native_tools=/absolute/retained-verified-native-tools
gt_runtime=/absolute/selected-external-runtime
GUARDTRELLIS_CURSOR_RUNTIME="$gt_runtime" \
  /bin/sh "$gt_native_tools/scripts/guardtrellis.sh" prepare <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

Expected checked text is `Repeat after me: Mira [PII] [PII].` The name remains.
Metadata goes to stderr. Selected secret signatures run first; secrets, mixed
secret/PII input and unavailable/error checks withhold the draft. Names,
unsupported contact forms, attachments, history and other context are outside
coverage. Raw input belongs on stdin, not in an argument/chat/attachment.

Only a separate deliberate Terminal action requests native review. Require the
complete explicit target; bare `prepare --open` and partial options are refused:

```sh
gt_cursor_user_data=/absolute/approved-existing-cursor-user-data
gt_cursor_extensions=/absolute/approved-existing-cursor-extensions
gt_cursor_profile=GuardTrellis-Isolated
GUARDTRELLIS_CURSOR_RUNTIME="$gt_runtime" \
  /bin/sh "$gt_native_tools/scripts/guardtrellis.sh" prepare --open \
  --user-data-dir "$gt_cursor_user_data" \
  --extensions-dir "$gt_cursor_extensions" \
  --cursor-profile "$gt_cursor_profile" <<'GT_SYNTHETIC'
Repeat after me: Mira mira@example.org +12025550123.
GT_SYNTHETIC
```

Use existing canonical separate nonoverlapping user-data/extensions directories
outside normal IDE roots and an already-open approved instance/workspace with an
empty draft. This is editor activation, not bundle verification; a closed selected
instance may launch. Only accepted checked text enters the fixed installed desktop
CLI, with a minimal environment and no unscoped OS/default-profile fallback.

[Prompt deeplinks](https://cursor.com/docs/reference/deeplinks) require review.
The shipped Cursor 3.27.22 CLI recognizes --open-url; this is not a guarantee across
versions or of the exact destination workspace/window. Inspect masked text,
destination and attachments; Cancel if wrong or valuable existing text is present.
Review/Create Chat is not Send; the helper never sends. A timeout/error may follow
handoff; inspect before a deliberate manual retry, with no automatic fallback.
This does not sanitize other context or establish no auxiliary traffic/retention.

The accepted preview.4 runtime was observed after native loading through the
actual product command, masked review and automated Escape to an empty draft.
This documentation-only refresh has new checksums and is not itself whole-package
host-tested; the executable/configuration/runtime mapping must remain exact.
Prior preview.3 callback/owner-assisted Cancel remains historical. Native prompt
behavior, stable trust, failures/bypasses and downstream suppression stay unverified.
Runtime tag 0.1.0-preview.1-sdk0.1.9 remains intentional and does not silently upgrade.
