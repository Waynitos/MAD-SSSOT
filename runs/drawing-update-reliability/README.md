# MAD Run: Drawing Update Reliability — Two-Phase Clean Sweep (v1.0.4)

**Date:** 2026-11-26  
**Topic:** Phase 2 drawing update and save after models are already renamed  
**Trigger:** RMAD (user request after repeated incomplete drawing saves)

## Outputs

- [AA-output.md](AA-output.md) — Strongest case FOR the v1.0.4 reliability patches
- [DA-output.md](DA-output.md) — Strongest case AGAINST further code changes
- [SSA-output.md](SSA-output.md) — Synthesiser verdict

## SSA Summary

Apply the v1.0.4 patches (RevisionTags/RevisionClouds Try/Catch, Frame_ skip, oNameOverrides re-run fallback, drawing re-open) and re-run Phase 2 on the current E2532-6 drawings. Do not add further features until the drawings are confirmed saved.

## Next Action

Open `PJ00204-GTA-3440-6-000001.dwg`, run Phase 2 → Apply In-Place Renames, and verify `P2-DWG-SAVED (Full/Solved)` lines for all included drawings.
