# RMAD — Merging old Traverse functions into Super Clean Sweeper

**Date:** 2026-11-05
**Topic:** Combine the old Traverse rule's occurrence-level Replace with the Super Clean Sweeper's SaveAs + provenance architecture so a full GA resweep produces the same result the old rule gave.

## Evidence
- v2.2.1 run 2026-11-05 11:06 on PJ00205-E3432-8-NEW E8 TOP GENERAL ASSEMBLY.iam.
- Phase 1: 257 files mapped (collision-suffixes working).
- Phase 2: 257 saved, 0 failed.
- Phase 3: 308 refs fixed, 0 failed; several P3-SAVE-FAIL with E_FAIL.
- Post-rule tree: TANK UPPER ASSEMBLY under new path; its children (TANK PLATFORM ASSEMBLY, GRATING, HANDRAIL ASSY) still point at old PJ00161 locations. Non-std parts updated.

## Outputs
- `AA-output.md` — add post-Phase 3 occurrence Replace on the active GA.
- `DA-output.md` — do not merge; the E_FAIL is Vault, and File.Copy must not return.
- `SSA-output.md` — add the occurrence Replace pass; keep SaveAs; defer browser rename.

## SSA verdict
Add a post-Phase 3 occurrence Replace pass on the active GA. Do not bring back File.Copy. Browser rename is deferred.
