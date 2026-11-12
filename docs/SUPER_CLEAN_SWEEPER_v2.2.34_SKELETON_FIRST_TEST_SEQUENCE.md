# v2.2.34 Frame Generator — skeleton-first controlled test sequence

User-proposed sequence for repairing a previously copied nested frame during rerun:

1. **Skeleton first:** identify and copy the target driving/reference skeleton(s), preserve expected folder context and verify no unintended original-project dependencies.
2. **Frame assembly second:** copy or relink the frame assembly and generated members using Inventor-supported reference handling; verify the frame resolves the intended new skeleton.
3. **Update after references resolve:** activate the appropriate assembly context and invoke an Inventor/Frame Generator update only after verifying the supported API/command for Inventor 2025; do not blindly assume `AFG_Refresh` exists or is sufficient.
4. **Save and verify:** capture dirty states, preflight write/Vault ownership, determine the safe save order empirically, save with journal/recovery safeguards, and compare references and frame editability afterward.

**Critical distinction:** copy/relink order is not necessarily save order. A skeleton may need saving in the context of its parent frame assembly. Do not silently force save or refresh on read-only, checked-in, or externally referenced files.

## Reproduction
Initial GA/GA drawing sweep leaves an old nested subassembly. A rerun replaces the nested sub successfully, but a subsequent save prompts for a Frame Generator skeleton as if it were checked in even though its checkout state appears different. Capture exact dialog, path, dirty state and Vault status.

## Test matrix
- Skeleton-first vs parent-first copy/relink order.
- Frame assembly active vs GA active during update.
- Update before save vs after save; track dirty state propagation.
- Save skeleton alone vs save with parent assembly context.
- Nested frames, checked-in/read-only skeleton, missing member, external master sketch and Content Center dependencies.

**Gate:** no production mutation until reference graph, preflight, save behavior, rollback and post-update readback are verified on disposable Inventor 2025 assemblies. Retain v2.2.33 performance profiling.
