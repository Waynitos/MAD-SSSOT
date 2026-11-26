# SSA — Synthesiser Verdict: Drawing Update Reliability in Two-Phase Clean Sweep

**Topic:** Phase 2 drawing update and save after models are already renamed.  
**Date:** 2026-11-26

## Verdict

Apply the v1.0.4 patches immediately and re-run Phase 2 on the current E2532-6 drawings. Do not add further features until the 34 drawings are confirmed saved.

### Reasoning

- The AA case is correct on the immediate failure mode: an unguarded `RevisionTags.Count` aborted every drawing before `Save2`. The Try/Catch (and the parallel one on `RevisionClouds`) is necessary and sufficient to let the existing save path complete.
- The oNameOverrides fallback is also justified for this specific situation. The models are already renamed; the drawings still point at the old names. The fallback lets a second Phase 2 run finish the job without forcing the user to empty folders or re-copy.
- The DA case is correct that COM interop remains fragile and that re-run logic can mask deeper issues. Those concerns are real, but they are not a reason to leave the drawings unsaved. The patches are small, localised, and do not change the two-phase architecture.
- Frame_ skip and the final drawing re-open are low-risk quality-of-life improvements that reduce noise and match user expectation.

### Required actions

1. Use the updated rule (v1.0.4) that contains:
   - Full Try/Catch around RevisionTags and RevisionClouds loops.
   - `\Frame_` skip in UpdateRenamedAssembliesInPlace.
   - oNameOverrides fallback inside UpdateRenamedDrawingsInPlace.
   - Visible re-open of the GA drawing at the end of Phase 2.
2. Open `PJ00204-GTA-3440-6-000001.dwg`, run **2. CLEAN SWEEP RENAME PHASE**, and click Apply In-Place Renames.
3. Confirm in the log that every included drawing produces a `P2-DWG-SAVED (Full/Solved)` line and that the drawing opens on screen at the end.
4. Only after that confirmation, evaluate whether any further architectural work (SQLite control plane, separate session, etc.) is warranted.

### Residual uncertainty

- Other COM members may still throw on certain Inventor releases or drawing contents. The outer Try/Catch in UpdateRenamedDrawingsInPlace will log them, but the drawing will be skipped. If that occurs, the log will name the exact member.
- Memory behaviour on the next equipment (E1732-4) is untested with the full Update2(True) path.

**SSA recommendation:** Ship v1.0.4, re-run Phase 2 on E2532-6, and stop iterating on the drawing path until the results are verified.
