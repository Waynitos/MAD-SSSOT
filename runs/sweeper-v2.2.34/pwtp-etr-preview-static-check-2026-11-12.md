# PWTP ETR preview-only source check — 2026-11-12

**Status: IMPLEMENTED experimental preview; NOT a complete Existing Target Repair candidate; NOT Inventor-tested.**

## Artifact
- Branch: `feature/sweeper-v2.2.34-existing-target-repair`
- File: `scripts/ilogic/experiments/PWTP_ETR_PREVIEW_ONLY.iLogicVb`
- Commit: `c38bf885eafc653365fbe1f76061087a140479c3`
- Purpose: inventory the currently active, already-copied target assembly and its referenced documents without modifying Inventor models. Output TSV in OS temporary directory.

## Static source checks (read back committed file)
- PASS: no document Save/Save2/SaveAs call.
- PASS: no ComponentOccurrence.Replace call.
- PASS: no File.SetAttributes or File.Copy call.
- PASS: read-only files flagged BLOCKED; outside-target files flagged EXTERNAL.
- PASS: target-root candidates still BLOCKED because Vault checkout/provenance are not verified.
- PASS: cycle guard and 100-level recursion limit.
- PASS: Frame Generator is only marked as a heuristic candidate, not positively identified.
- PASS: output goes to `Path.GetTempPath()` and does not overwrite engineering models.
- LIMITATION: these are source-text checks, not VB/iLogic compilation or Inventor API execution tests.
- LIMITATION: the diagnostic uses `ReferencedDocuments`, which may omit suppressed/unresolved descriptors and does not enumerate individual occurrence paths. It is NOT an authoritative repair plan.
- LIMITATION: no preview approval UI, transaction journal, rollback executor, reference integrity verification, collision resolution, Vault API checkout validation or retained profiler integration yet.

## Next PWTP
1. Improve read-only preview to capture `ReferencedDocumentDescriptors`, per-occurrence parent paths and exact source/target identity with collision provenance.
2. Extract existing profiler hooks and Phase 3/4 call graph from actual source.
3. Implement explicit opt-in mutation only on disposable checked-out test models, with journal, rollback, save/reopen validation and Frame Generator integrity checks.
4. Re-run static checks on the integrated candidate, then seek separate user-run Inventor verification.

**No release readiness claim. No changes to production/main.**
