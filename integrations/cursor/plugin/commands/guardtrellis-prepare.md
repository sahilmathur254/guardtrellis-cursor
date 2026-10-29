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
explicit prepared SDK0.1.9runtime:

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

Only a separate deliberate Terminal `prepare --open` requests Cursor's native
review flow. It is editor activation, not bundle verification. Start with an empty
draft in the intended workspace/This Mac, inspect checked text and attachments,
and Cancel on wrong destination or valuable existing text. Review/Create Chat
is not Send; the helper never sends. It does not sanitize other attached context
or establish no auxiliary traffic/provider retention.

Preview.3 has not been tested in a real Cursor host. Earlier preview.2 masked
review → Cancel used an explicit-profile CLI launcher callback in a named profile
sharing application/account state. The bundled default opener remains unverified;
this is not current-package acceptance or provider suppression. Runtime tag
0.1.0-preview.1-sdk0.1.9 remains intentional and does not silently upgrade.
