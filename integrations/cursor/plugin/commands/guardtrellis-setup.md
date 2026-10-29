---
name: guardtrellis-setup
description: Explain explicit Terminal runtime preparation and reviewed project-helper staging.
---

Provide instructions only. Do not install packages, execute setup, stage/activate
hooks, launch Cursor, alter trust or submit anything automatically. This command
is agent guidance, not a local dialog or a pre-provider boundary.

Native/delivery0.1.0-preview.3 uses SDK0.1.9. The external runtime identity remains
`0.1.0-preview.1-sdk0.1.9` deliberately; do not migrate/reuse an unknown environment
because the name matches. Preview.3 has not been tested in a real Cursor host.
Earlier preview.2 loading/restart/removal and local readiness do not certify
new-package prompt behavior, stable trust or downstream suppression.

The user needs the authenticated complete helper bundle, an unopened approved
workspace, trusted existing Python3.12/uv and a fresh external runtime. The inner
native ZIP alone does not include the workspace installer. In Terminal, retain a
verified native-tools copy outside bundle/workspace/runtime for later SDK removal:

```sh
gt_python=/absolute/trusted/python3.12
gt_uv=/absolute/trusted/uv
gt_native_tools=/absolute/retained-verified-native-tools
gt_runtime=/absolute/new-external-runtime
"$gt_python" -I -B "$gt_native_tools/scripts/runtime_setup.py" \
  setup --python "$gt_python" --uv "$gt_uv" --dest "$gt_runtime"
"$gt_python" -I -B "$gt_native_tools/scripts/runtime_setup.py" doctor --dest "$gt_runtime"
```

Initial explicit setup may fetch frozen dependencies from PyPI; it downloads no
Python and makes no AI-provider request. Prompt handling never installs packages.
Then show README's complete-helper `plan/install/health` steps. Plan is read-only;
install requires selected-project review and stages one owned workspaceOpen entry.
Opening/reloading that workspace is separate activation. --runtime does not set
a running GUI's environment; a later approved process must receive the same
GUARDTRELLIS_CURSOR_RUNTIME. Do not activate a normal profile as a shortcut.
Explain advisory continuation, unavailable state and metadata-only support.
