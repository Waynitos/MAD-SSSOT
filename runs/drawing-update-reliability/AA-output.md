# AA — Advocate: Strongest Case FOR the v1.0.4 Drawing Reliability Fixes

**Topic:** Ensuring Phase 2 of the two-phase Clean Sweep rule always updates and saves all drawings after models have been renamed.

## Strongest Case FOR

The v1.0.4 changes directly address the root cause of the previous failure (unguarded `oSheet.RevisionTags.Count` aborting every drawing before `Save2`) and add the missing re-run path.

1. **Try/Catch around RevisionTags and RevisionClouds** — Inventor’s COM interop for `Sheet` does not always expose `RevisionTags`. An unguarded access threw and jumped to the outer Catch, skipping the save. Wrapping both loops means cleanup can never abort the save path again. This is the single highest-leverage fix.

2. **oNameOverrides fallback in UpdateRenamedDrawingsInPlace** — On a second Phase 2 run the models are already renamed, so `oFinalMoveMap` is empty. The fallback reconstructs the new path from the name override and the original directory, then calls `ReplaceReference` if the target exists. This lets the user re-run Phase 2 on the already-renamed tree and still update every drawing without re-copying or re-moving files.

3. **Skip \Frame_ folders** — Eliminates the five harmless but noisy E_FAIL entries on Frame Generator skeleton parts that are not renamed in Phase 2.

4. **Re-open the GA drawing at the end of Phase 2** — Matches the Phase 1 behaviour and puts the updated drawing in front of the user immediately.

These four changes convert a brittle, one-shot process into a re-runnable, fault-tolerant drawing update pass. Every drawing that has its references successfully repointed will now reach `Save2(False)` with `Update2(True)` already applied, producing Vault-ready, fully solved drawings.

The architecture of the two-phase rule is already correct; these are surgical reliability patches, not a redesign. Applying them and re-running Phase 2 on the current E2532-6 drawings will finish the job that the previous run aborted.
