# PWTP Existing Target Repair — preview-only experiment v0.1.0
**Status: IMPLEMENTED / STATICALLY INSPECTED / NOT INVENTOR TESTED. NOT A COMPLETE REPAIR CANDIDATE.**
**Date:** 2026-11-13. **Branch:** `feature/sweeper-v2.2.34-existing-target-repair`.
**Profiler baseline:** `diagnostic/sweeper-v2.2.33-profiler`; existing full rule remains unchanged.

## Evidence and source
Experimental standalone rule: `scripts/ilogic/experiments/SCS_EXISTING_TARGET_REPAIR_PREVIEW_v0_1_0.iLogicVb`.
Inspected monolithic rule `scripts/ilogic/TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb` (221,256 characters, source header v2.2.32), plus `runs/sweeper-v2.2.34/pwtp-source-gate-inventory-2026-11-12.md`.
The baseline Phase 4 save path can clear read-only attributes; the Phase 2 fallback may copy raw bytes without repaired references. Neither path is invoked by this experiment.

## Experiment
Open an already-copied target assembly; run as external iLogic rule; enter distinct PJ##### old/new prefixes; inspect `%TEMP%\SCS_Repair_Previews\repair_preview_*.tsv`.
Rule examines direct assembly document descriptors and proposes a same-directory target filename for references beginning with the old project prefix. Every existing match is labelled **CANDIDATE_UNVERIFIED**, not approved for replacement. Missing targets and read-only targets are blocked. It logs total elapsed milliseconds and displays them in the final popup. It does not modify Inventor documents or file attributes.

## Source-level checks actually performed
- Reviewed rule source for absence of `Save`, `Save2`, `SaveAs`, `ReplaceReference`, `File.Copy` and `SetAttributes` calls: **PASS** (source text check).
- Explicit read-only bitmask comparison `<> 0`: **PASS** (source text check).
- Stopwatch and final elapsed-milliseconds popup: **PASS** (source text check).
- Preview-only label and no implicit execution: **PASS** (source text check).
- Inventor compilation: **NOT RUN**. Inventor runtime tests: **NOT RUN**.

## Critical limitations — do not use as a repair executor
- No nested assembly traversal, no occurrence-specific provenance, no frame skeleton/member identity validation.
- Same-directory filename inference is **not** sufficient to establish correct target path, ancestry, copy provenance, GUID/InternalName compatibility, or uniqueness.
- No Vault checkout/lock detection; no write-permission validation beyond read-only attribute; no collision resolution or ownership verification.
- No mutation, backup/journal, rollback, reopen/rescan or reference-integrity proof.
- No per-function timing comparison to baseline; only elapsed preview duration.
- API surface is deliberately late-bound for document descriptors; actual Inventor 2025 compile/runtime compatibility remains to be tested.
- The rule's log is a candidate list, not an execution plan or release approval.

## Next PWTP gate
MU runs this disposable/read-only diagnostic in Inventor 2025 on problematic FG assembly, parent and GA; capture logs and errors. Before any write-capable candidate, implement complete graph/provenance preview, Vault fail-closed preflight, verified rollback transaction, frame associativity checks, reopen-based integrity validation, and retained profiler measurements. Test only on isolated disposable copies.
