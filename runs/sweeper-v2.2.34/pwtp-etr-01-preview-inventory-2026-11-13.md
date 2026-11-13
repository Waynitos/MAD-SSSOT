# PWTP-ETR-01 — Existing Target read-only inventory (2026-11-13)

**Status: IMPLEMENTED (experimental), STATICALLY REVIEWED, NOT Inventor-tested. NOT a complete v2.2.34 repair candidate.**

Branch: `feature/sweeper-v2.2.34-existing-target-repair` based on `diagnostic/sweeper-v2.2.33-profiler`.

## Deliverable
`scripts/ilogic/experiments/SCS_EXISTING_TARGET_REPAIR_PREVIEW_v0_1.iLogicVb`

Standalone iLogic diagnostic for an already-copied target assembly. Enumerates transitive `ReferencedDocuments` edges, path existence, file read-only attributes, file sizes, dirty states, elapsed milliseconds and errors. Outputs TSV under `%TEMP%\SCS_ETR_Preview` and a final popup with total elapsed time. It never saves, copies, replaces references, checks out Vault files or changes file attributes. No actual repair plan is produced: this is an inventory precursor only.

## Source-level checks (not compiler or Inventor runtime tests)
- Source contains one `Sub Main`, one recursive `Sub Walk`, two helper functions and matching end declarations.
- Stopwatch starts at entry, emits elapsed milliseconds for records and summary; popup includes total time and version.
- All discovered references are classified `UNVERIFIED`; final status always `MUTATION_BLOCKED`.
- Source has no calls to `Document.Save`, `Save2`, `SaveAs`, `ComponentOccurrence.Replace`, `File.Copy` or `File.SetAttributes`. The `String.Replace` calls in `Clean` are log-field sanitation, not Inventor reference replacement.
- Read-only attributes are observed only; Vault checkout status is **unknown** and no mutation is permitted.
- Exception paths record errors; recursive walk has a depth cap and cycle suppression.
- Static source review does **not** establish iLogic compilation, API compatibility, completeness of graph traversal, Frame Generator identity preservation or performance.

## Limitations / risks
- `ReferencedDocuments` does not capture every occurrence identity, suppressed/model-state reference, drawing/IPN reverse reference, or Frame Generator associativity. It may also load dependencies. No FG-specific copy or repair operation exists.
- File-level read-only flags cannot establish Vault ownership/checkout permissions.
- Source-level check of `Dirty` and reference enumeration must be validated in Inventor 2025. No claims of runtime success.
- No preview mapping, collision handling, journal, rollback, reopen validation, source-target provenance proof, Vault preflight or retained v2.2.33 profiler integration yet.

## Next experiment
Run on disposable target frame, parent and GA in separate clean sessions, collect TSV and compare identities, timing, dirty states and missing edges. Next implement a **deterministic preview-only source-to-target mapping**, then collision/Vault fail-closed preflight, backed-up transactional repair and post-reopen integrity verification. Preserve v2.2.33 profiler baseline. Do not merge or deploy.

## Evidence
Earlier source-gate inventory: `runs/sweeper-v2.2.34/pwtp-source-gate-inventory-2026-11-12.md`.
