# SSA — Merging old Traverse functions into Super Clean Sweeper

**Verdict:** Add a post-Phase 3 occurrence Replace pass on the active GA. Do not bring back the old File.Copy path. Browser rename is deferred.

**Evidence weighed**
- 257 files saved, 308 refs fixed. The SaveAs architecture works.
- The remaining old paths are in assemblies that had P3-SAVE-FAIL with E_FAIL.
- The old Traverse rule's occurrence-level Replace on the live assembly is what produced a fully updated GA tree.
- File.Copy kept the original GUID — that path must not return.

**Decision**
1. **Add a post-Phase 3 occurrence walk.** Walk the active GA's ComponentOccurrences. For any occurrence whose current path is in oActualMap and whose target exists, call ComponentOccurrence.Replace(newPath, False). Unsuppress first if needed, re-suppress after. This uses the new architecture's map, not the old File.Copy path.
2. **Do not retry the E_FAIL saves in the same pass.** Log them. The occurrence Replace is the fallback for those assemblies.
3. **Browser rename is deferred.** It is cosmetic and not required for the resweep result.
4. **Keep the SaveAs + provenance base.** No File.Copy for the main path.

**Next action:** Implement the post-Phase 3 occurrence Replace pass, re-run on the same GA, and confirm the tree shows the new paths for TANK PLATFORM, GRATING, and HANDRAIL.
