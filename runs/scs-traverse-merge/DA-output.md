# DA — Merging old Traverse functions into Super Clean Sweeper

**Position:** The Super Clean architecture is already correct. Merging old Traverse functions will not fix the remaining gaps and risks breaking the provenance model.

The 11:06 run fixed 308 refs. The remaining old paths are in assemblies that had P3-SAVE-FAIL with E_FAIL — Vault refused the save. An occurrence-level Replace after Phase 3 will hit the same Vault lock. The old Traverse rule used File.Copy which kept the original GUID. Bringing its occurrence-level logic back into Super Clean risks reintroducing the GUID problem the new architecture was built to solve. Browser rename is cosmetic and not the priority. The correct next step is to retry the E_FAIL saves after a Vault checkout, or accept those refs as external.

**Recommended stance:** Do not merge the old Traverse occurrence walk. Retry the E_FAIL saves after confirming the files are checked out, or leave those refs pointing at the originals. The SaveAs + provenance architecture is the right base.
