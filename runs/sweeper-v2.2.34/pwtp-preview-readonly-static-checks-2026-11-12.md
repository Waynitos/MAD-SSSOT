# PWTP v2.2.34 — Existing Target Repair preview experiment (2026-11-12)

**Status: IMPLEMENTED (preview-only); static inspection performed; NOT Inventor tested; NOT complete repair candidate.**

Commit `26854e4` added `scripts/ilogic/experiments/EXISTING_TARGET_REPAIR_PREVIEW_READONLY.iLogicVb` to the isolated feature branch. Source reads the active existing-target assembly, recursively reports referenced documents, file read-only and dirty flags, and CS_SourcePath provenance, and emits a TSV under `%TEMP%\SCS_Repair_Previews`. No model file mutation is intended.

## Source-level checks (direct fetch of committed 3,849-character source)
- PASS: explicit active assembly and saved-file gates.
- PASS: recursive `ReferencedDocuments` traversal, cycle guard and depth limit.
- PASS: fail-closed labels for missing file, read-only attribute, unknown attributes, unknown provenance, dirty document and reference enumeration error.
- PASS: no `Save`, `Save2`, `SaveAs`, `File.Copy`, `ReplaceReference`, `SetAttributes` or Vault `CheckOut` operation calls in executable code.
- Static scan initially returned false-positive on `String.Replace` in the TSV escaping helper; verified it is string sanitation, not an Inventor component replacement. This demonstrates that source scans need API-aware matching.
- NOT TESTED: iLogic/VB compilation, actual Inventor reference enumeration, Vault state, performance, Frame Generator associativity, collision checks, rollback and persisted reopen validation.

## Explicit limitations and next gates
1. This is a **document-level preview**, not occurrence-level path mapping: repeated occurrences are collapsed by the visited set. Record `ComponentOccurrence` and `FileDescriptor` edges before planning mutations.
2. The presence of `CS_SourcePath` is not proof of trustworthy provenance. Require source-target identity, project-root and collision verification.
3. Read-only attributes do **not** prove Vault checkout; unknown Vault state must block mutation.
4. Frame Generator skeleton/member linkage and generated file naming require explicit inventory and read-only evidence.
5. A rollback promise requires a pre-mutation snapshot, complete journal, verified restoration and fault-injection tests on disposable copies.
6. Existing profiler timing must be preserved when integrating the planner and executor.
7. Do not integrate preview into production or enable writes before all gates pass and Inventor testing is performed.

The isolated experiment is a PWTP increment, not the requested complete Existing Target Repair candidate. Production/main and profiler baseline are unchanged.
