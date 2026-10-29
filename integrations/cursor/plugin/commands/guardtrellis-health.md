---
name: guardtrellis-health
description: Explain Terminal checks that separate configuration, local runtime and native observations.
---

Provide instructions only. Do not read real prompts, clipboard, account data,
normal-profile history or raw host logs. Do not launch/reload Cursor, activate
hooks or send a request to test them. This slash command is agent guidance and
may itself already be processed by the host/provider.

With the authenticated complete helper bundle and retained verified native-tools,
the user can run in Terminal:

```sh
gt_python=/absolute/trusted/python3.12
gt_helper=/absolute/verified-helper-bundle/scripts/cursor_workspace.py
gt_workspace="/absolute/approved workspace"
gt_native_tools=/absolute/retained-verified-native-tools
gt_runtime=/absolute/selected-external-runtime
"$gt_python" -I -B "$gt_helper" health --workspace "$gt_workspace"
"$gt_python" -I -B "$gt_helper" health --workspace "$gt_workspace" --check-runtime
"$gt_python" -I -B "$gt_native_tools/scripts/runtime_setup.py" doctor --dest "$gt_runtime"
```

Default helper health inspects source/configuration without SDK execution.
Explicit --check-runtime runs synthetic local probes; runtime unavailability is
nonzero while configuration state stays separate. CLI readiness does not observe
GUI environment, trust, last hook execution or downstream suppression. Runtime
identity0.1.0-preview.1-sdk0.1.9 stays independent of native/deliverypreview.3;
a marker is not interpreter authenticity or permission to reuse/delete a runtime.
Preview.3 has not been tested in a real Cursor host. Earlier preview.2
loading/restart/removal and separate component UI are bounded prior evidence,
not this package's native prompt acceptance.
Use metadata-only manually reviewed support; never upload full health output with
private paths, prompts, source or native logs. Do not install missing dependencies
automatically during an agent request.
