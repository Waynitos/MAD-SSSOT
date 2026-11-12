# PWTP Existing Target Repair — source-level gate inventory (2026-11-12)

**Status: INVESTIGATING — incomplete candidate; not Inventor-tested.**

## Inspected baseline
- Branch: `diagnostic/sweeper-v2.2.33-profiler`
- Comparison branch: `feature/sweeper-v2.2.34-existing-target-repair`
- File: `scripts/ilogic/TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb`
- SHA on both branches at inspection: `a45cc8d0bbc5ff47792f565d02aca6076e651f2b` (same 221,256-character source). The source header identifies v2.2.32, despite the profiler branch name: branch naming alone is not evidence of implementation version.

## Source-level findings
1. Main `Sub Main()` begins with active assembly/drawing resolution. An Existing Target Repair path must not reuse the new-copy entry point without separating target ownership and mutation permissions.
2. Phase 2 `SaveAs(sNewFull2, True)` falls back to raw `File.Copy`. Copy success is not proof of repaired internal Inventor references. Do not promote a raw copy to VERIFIED.
3. The Phase 2 post-copy code clears the ReadOnly attribute on newly created files. A repair path must never inherit this behaviour for pre-existing targets, particularly Vault-controlled files.
4. Phase 4 save path explicitly calls `File.SetAttributes(sThisFull, ... And Not ReadOnly)` immediately before `oDoc.Save2(False)`. This is an unsafe pattern for Existing Target Repair; it must be gated or replaced with a fail-closed read-only/Vault preflight.
5. Phase 4 `P4-SAVE-FAIL` logs errors but the surrounding resweep may still report successful replacements. A repair transaction must distinguish in-memory replacement from committed, reopened reference integrity.
6. No `Stopwatch` literal found in inspected source; profiling implementation and retention need more targeted inspection rather than assuming instrumentation is present.

## Required candidate gates
- Preview-only plan, target/source identity and provenance evidence, parent dependency order, and frame detection.
- Explicit collision resolution (never overwrite unknown existing targets).
- Read-only, Vault checkout and write-permission validation; fail closed if status cannot be established.
- Backup/journal and compensating rollback plan before modifying a target, including partial save failure.
- Verify every replaced occurrence and FileDescriptor reference, reopen targets and check for old paths, preserve Frame Generator skeleton/member associativity.
- Preserve profiler measurements with phase timings and errors, not just total duration.
- Source-level static checks and test fixture evidence; no Inventor execution claims.

## Next smallest PWTP sprint
Extract the precise Phase 4 save/resweep and Phase 3 descriptor-repair functions, identify their call graph and current instrumentation, then implement a **preview-only repair plan** that emits deterministic proposed operations with no Inventor writes. Gate mutation behind an independently reviewed preflight and journal.

No production/main modifications made. This record is not a release candidate or evidence of passing tests.
