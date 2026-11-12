# PWTP-02 — Existing Target Repair: exact Phase 4 failure boundary and minimal experiment

**Status:** INVESTIGATING. Source inspection only; no Inventor compilation, execution or production changes.

## Baseline inspected
- `diagnostic/sweeper-v2.2.33-profiler` baseline and `feature/sweeper-v2.2.34-existing-target-repair` source file `scripts/ilogic/TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb`.
- Blob SHA: `a45cc8d0bbc5ff47792f565d02aca6076e651f2b`, header v2.2.32.
- Existing run data: local frame `PJ00183-346-V0-10-F.iam` logged five `P4-REPLACE` operations, then `P4-SAVE-FAIL` and `P4-GA-SAVE-FAIL` with HRESULT 0x80004005. The five replacements are **not evidence of persisted reference repair**.

## Source-level observations
1. `P4-REPLACE` increments `iFixed` after an immediate in-memory path check. The recursive walk later attempts to save the target-folder assembly separately.
2. The Phase 4 save block explicitly obtains `File.GetAttributes(sThisFull)`, clears `ReadOnly` using `File.SetAttributes`, and calls `oDoc.Save2(False)`. This is unsafe for pre-existing Vault targets and must **not** be reused for Existing Target Repair.
3. The `P4-SAVE-FAIL` catch logs the error and continues; no durable commit verification or rollback follows. Hence a positive `iFixed` count can coexist with failed persistence.
4. `P3-FD-FAIL` and `P3-FD-SKIP(locked)` are already distinct diagnostics, but they are not a transactional repair protocol.
5. Source contains `dtStart`/elapsed-time reporting but no literal `Stopwatch`. A v2.2.33 profiler branch name is not sufficient to establish phase-level instrumentation; measure and preserve actual existing counters before changing them.

## Proposed transaction states (no implementation claim)
`DISCOVERED -> PREVIEWED -> PREFLIGHT_PASSED -> BACKED_UP -> MUTATING -> SAVED -> REOPEN_VERIFIED -> COMMITTED`; any error after BACKED_UP enters `ROLLBACK_PENDING`, then `ROLLED_BACK` only after restored file identity and references are verified. On inability to restore, mark `BLOCKED_MANUAL_RECOVERY`.

## Minimum safety gates before any write
- **Target identity:** full canonical source/target paths, existing provenance `CS_SourcePath`, expected `InternalName`, and collision ambiguity checks; refuse missing or mismatched provenance.
- **Vault:** require positive checkout/write authority established via supported Vault mechanism; unknown status blocks. Read-only filesystem bit must never be cleared by repair.
- **Reference closure:** preview every old occurrence and file-descriptor reference, including nested frame skeleton/member dependencies; reject unresolved, cyclic, or duplicate target mappings.
- **Backup:** isolated copy of each authorised target with hash, path, timestamp and rollback journal; confirm all backups before first mutation. Restoration cannot be called successful until Inventor is closed/released and files reopen with expected graph.
- **Save verification:** record separately `IN_MEMORY_REPLACED`, `SAVE_SUCCEEDED`, `REOPEN_REFERENCE_VERIFIED`; a frame parent save must not imply GA save.
- **Performance:** preserve elapsed reporting and collect per-stage durations, count of opened documents, saves, failures, and reference operations.

## Next executable PWTP experiment
1. Use a disposable, isolated copy of the problematic frame with its skeleton and generated members; never modify checked-in source or production folder.
2. Run the already committed **read-only** `FRAME_CONTEXT_DIAGNOSTIC_READONLY.iLogicVb` directly on the frame, then on parent and GA; archive logs and any compilation errors.
3. Add occurrence-path and FileDescriptor snapshot logging only after the first rule compiles. Verify path normalization and reference enumeration on a known small fixture.
4. Only then build a **preview-only** target-repair planner with deterministic operation IDs and collision/Vault flags; test against synthetic fixture graphs before adding any mutation path.
5. Run copy/save trials only with explicit permission on disposable files and compare the independently opened frame vs GA-open context.

## Static test acceptance matrix
- Missing target provenance -> BLOCKED (no writes).
- Different source paths resolving to same existing target -> BLOCKED (no suffix overwrite).
- Read-only or unknown Vault checkout -> BLOCKED (no attribute mutation).
- Missing skeleton/member reference -> BLOCKED (no frame promotion).
- Immediate replacement succeeds but parent Save2 fails -> FAILED_SAVE, not VERIFIED.
- Parent saves but GA fails -> INCOMPLETE, not COMMITTED.
- Backup creation fails -> BLOCKED before mutation.
- Rollback cannot reopen/verify original graph -> BLOCKED_MANUAL_RECOVERY.
- Complete graph verified after reopen -> eligible for COMMITTED.
- All phase timing and operation counts retained -> performance gate passes.

**No release candidate is claimed.** This record preserves an evidence-driven, fail-closed path for the next implementation sprint.
