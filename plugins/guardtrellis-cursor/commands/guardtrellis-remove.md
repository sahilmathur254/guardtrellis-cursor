---
name: guardtrellis-remove
description: Explain safe project-helper removal and separate owned-runtime cleanup.
---

Provide instructions only. Do not change configuration, delete source, remove a
runtime, uninstall anything, close/restart Cursor or contact support automatically.
First identify the exact installation route. This guide covers the complete
workspace-helper bundle; it does not assume a normal global-cache install.

Close the entire owned Cursor process before removal. With the retained verified
complete helper bundle, the user can run in Terminal:

```sh
gt_python=/absolute/trusted/python3.12
gt_helper=/absolute/verified-helper-bundle/scripts/cursor_workspace.py
gt_workspace="/absolute/approved workspace"
"$gt_python" -I -B "$gt_helper" remove --workspace "$gt_workspace"
```

This removes recognized project source/control/entry, preserves unrelated hooks
and runtime, and reports native unload unobserved/restart required. Config editing
is not a reliable live unload. A separately approved fresh native process must
observe that loading stopped. Preview.3 has not been tested in a real Cursor host;
earlier exact preview.2 loading/restart/removal is bounded prior evidence only.

Only after the runtime is unused by other workspaces/profiles, use retained
verified native-tools outside the workspace. The installed project script was
removed with the helper source, so do not call it for SDK cleanup:

```sh
gt_native_tools=/absolute/retained-verified-native-tools
gt_runtime=/absolute/selected-external-runtime
"$gt_python" -I -B "$gt_native_tools/scripts/runtime_setup.py" doctor --dest "$gt_runtime"
"$gt_python" -I -B "$gt_native_tools/scripts/runtime_setup.py" remove --dest "$gt_runtime"
```

Runtime identity0.1.0-preview.1-sdk0.1.9 intentionally remains independent of source
preview.3. A matching tag does not prove ownership or authorize deletion. If
ownership/inventory/concurrent-state checks refuse, stop for local review. Never
use broad deletion, remove a shared environment/profile, edit a ledger or alter
trust/managed policy to force success. Updates/rollback require reviewed matching
artifacts and remove/reinstall, not silent live replacement. Removal does not
erase host/provider history or guarantee prompt egress prevention. Use metadata-only
support; send no raw prompts/source/Hook Input/debug logs or credentials.
