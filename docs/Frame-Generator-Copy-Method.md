# Frame Generator Copy Method (Recognized)

**Status**: Recognized / Proven  
**Date**: 2026-11-20  
**Context**: Inventor iLogic copy-design (TEST2 series / Clean Sweeper Mode 6)

## Problem

Frame Generator assemblies (`FrameDoc`) cannot be reliably copied with the normal Inventor APIs:

- `Document.SaveAs` fails with `0x80004005 (E_FAIL)`
- `ComponentOccurrence.Replace` inside an open assembly triggers the live Frame Generator engine and fails
- Even `_LibraryDocumentModifiable = True` does not allow SaveAs on the frame assembly

The frame assembly, its skeleton part (`SkeletonDoc`), and frame members (`FrameMemberDoc`) form a tightly coupled set. Inventor requires them to stay consistent and often refuses out-of-context SaveAs operations on the frame assembly alone.

## Recognized Method

**File-level copy + offline reference rewrite** using `ReferencedFileDescriptor.ReplaceReference`.

This approach bypasses the live Frame Generator engine entirely.

### Steps

1. Detect any document with the `FrameDoc` interest.
2. Collect the complete group:
   - Frame assembly
   - Associated skeleton part (`SkeletonDoc`)
   - Frame members (`FrameMemberDoc`)
3. Copy the entire group on disk to the target location (preserving relative structure / `\Frame\` subfolder if present) using `System.IO.File.Copy`.
4. Strip read-only attributes on the copies.
5. Open each copied `.iam` and `.ipt` invisibly (`Documents.Open(path, False)`).
6. For every `DocumentDescriptor` / `ReferencedFileDescriptor`:
   - If the referenced file is in the group map, call `ReplaceReference(newPath)`.
7. Call `Update2(True)` and `Save()` on the copies that had references rewritten.
8. Close the invisible documents.
9. Add the mapped paths to the main path dictionary so parent assemblies can still perform normal occurrence replaces.

### Why This Works

- `ReplaceReference` updates the underlying file pointers without activating the Frame Generator validation / UI engine.
- All derived skeleton links inside frame members are rewritten before any assembly is opened in a live session.
- The relative structure expected by Frame Generator is preserved.
- Matches the behaviour of Design Assistant / Pack & Go for independent FG copies, implemented programmatically.

### Proven Result

In TEST2 v1.0 (2026-11-20):

- Ordinary assemblies and parts continued to use the normal SaveAs + occurrence replace path.
- The two previously failing Frame Generator assemblies (`PJ00190-343-V0-11-F.iam` and `PJ00190-343-V0-10-10-10-F.iam`) took the special path.
- Both completed with `FG-SPECIAL-OK`.
- Overall result: **Saved 259 / 259 — Failed 0**.

## Implementation Notes

- The method is selective: only documents with `FrameDoc` (and their related skeleton/members) use the special path.
- Standard Content Center fasteners continue to be skipped by design.
- Vault add-in deactivation and prompt suppression remain useful during the run.
- Suitable for integration into a planner/executor architecture (e.g. SQLite-based copy-design control) where the planner records the FG group and the executor performs the copy + rewrite.

## References

- TEST2_LOGGED_v1.0_FG_FileCopy_ReplaceReference.iLogicVb
- Log evidence: TEST2_RUN_20261120_094156.log (FG-SPECIAL-OK on both previously failing frames)

---
*Documented as a recognized method for handling Frame Generator items in programmatic copy-design outside Vault.*
