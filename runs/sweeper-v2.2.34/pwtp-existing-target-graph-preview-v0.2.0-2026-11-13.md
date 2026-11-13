# PWTP Existing Target Repair graph preview v0.2.0 — 2026-11-13

**Status:** IMPLEMENTED (experiment); STATICALLY INSPECTED; NOT Inventor-tested; NOT a complete repair candidate.

**Branch:** `feature/sweeper-v2.2.34-existing-target-repair` based on `diagnostic/sweeper-v2.2.33-profiler`. Production/main and the existing monolithic rule remain untouched.

## Source and scope
`scripts/ilogic/experiments/SCS_EXISTING_TARGET_REPAIR_GRAPH_PREVIEW_v0_2_0.iLogicVb`, commit `7cf83100b3c5592e764134b08b4f4fd5bb95fd3e`.

Compared with v0.1.0 preview: recursively visits loaded assembly document references; reports inferred old-prefix/new-prefix target candidates, absent targets, read-only targets, self references and multiple source paths inferred to one target. Records overall and per-assembly elapsed milliseconds, and elapsed failure context. Logs TSV under `%TEMP%\SCS_Repair_Previews`. Final popup shows total elapsed time. No assembly mutation is attempted.

## Source-level checks performed (text inspection, not compiler execution)
- Recursive assembly scan present: PASS.
- Collision, missing-target and read-only status branches present: PASS.
- Stopwatch total, stage and error timings present: PASS.
- No calls to document Save/Save2/SaveAs/ReplaceReference/Update or File.Copy/Move/Delete/SetAttributes: PASS (source-text regex).
- Runtime Inventor 2025 iLogic compilation: NOT RUN.
- Autodesk API object semantics and traversal on Frame Generator documents: NOT VERIFIED.
- Nested occurrence-specific paths and document identity/provenance: NOT IMPLEMENTED.

## Fail-closed interpretation
Every proposed reference is `CANDIDATE_UNVERIFIED`, never an approved replacement. The inferred same-folder target is only a heuristic. Frame-related filename hints are not proof of Frame Generator identity or skeleton/member associativity. Vault checkout/locks, GUID/InternalName compatibility, permissions, dependency ordering, collision ownership, backups, rollback and reopened-document integrity remain unverified. A successful preview does not imply safe mutation.

## Next PWTP test
Run the read-only rule on the problematic frame assembly, its parent and GA in isolated/restored contexts; capture TSVs and any compilation errors. Compare timing and reference mapping. Do not attempt Existing Target Repair writes until Vault and frame preflight, provenance, rollback journal and reopened-integrity gates are implemented and tested on disposable copies.
