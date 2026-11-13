# PWTP Existing Target Repair — preview experiment v0.1.0 (2026-11-13)

**Status: IMPLEMENTED (experimental), STATICALLY CHECKED, NOT Inventor-tested, NOT a complete v2.2.34 candidate.**

Source: `scripts/ilogic/experiments/SCS_EXISTING_TARGET_REPAIR_PREVIEW_v0.1.0.iLogicVb`
Commit: `5a04287b5c5c9a8903fab10c8c0bf42be74a12fd`.
Existing main source remains unchanged and identifies as v2.2.32. Feature branch is based on `diagnostic/sweeper-v2.2.33-profiler`; branch naming does not prove profiling functionality.

## Scope and safety
Standalone, read-only Inventor 2025 iLogic preview. Requires active source assembly and a user-entered existing target directory. Enumerates recursive `ReferencedDocuments` and maps relative source paths to the selected target root; reports missing/external/read-only targets, ambiguous mappings, and unknown Vault/identity/frame integrity. All apparently writable targets remain REVIEW, never approved for mutation. No assembly saves, reference replacement, file copy, attribute clearing or Vault operations. TSV output in temporary directory is the only write. Does not modify production or Vault files.

## Source-level checks executed (all passed)
1. Mutation API absence: no Save, Save2, SaveAs, ReplaceReference, File.Copy or File.SetAttributes calls.
2. BBⁿ-PROF-001 preliminary: total stopwatch elapsed in popup/log, per-document traversal elapsed in log, version in every record.
3. Collision mapping dictionary check exists.
4. FileAttributes.ReadOnly inspection exists.
5. Target-root prefix guard exists.
6. Unverified Vault status is explicitly reported rather than asserted.
7. Error records and version labels present.

These are source-text assertions, not a VB.NET compiler, Inventor COM/API or Vault execution test.

## Known limitations / DA
- The mapping is intentionally a simple relative-path prototype, not the production prefix/rename planner. It will not infer actual previously copied target filenames.
- `ReferencedDocuments` deduplicates by document path and does not capture occurrence-level edges, suppressed/unresolved references, model-state nuances, or complete file descriptors.
- Recursive traversal can be expensive; timing rows include descendants, so do not interpret them as exclusive function timings.
- The root assembly itself is outside the source-root child prefix and is BLOCKED. This is intentional fail-closed behaviour for now.
- Windows path casing and symlinks/UNC aliases are not fully canonicalised.
- A non-read-only target is not evidence of Vault checkout, write permission, correct provenance or safe ownership.
- Frame Generator skeleton/member identity, context and associativity are **not inspected**; no repair is authorised.
- No rollback/journal is needed for the read-only preview, but mandatory before any write-capable candidate.
- Performance comparison requires actual equivalent Inventor runs; no measured runtime evidence exists.

## Next gates before v2.2.34 completion
1. Source-aligned preview planner using current `ResolveTarget`/provenance and occurrence/descriptor edges, with deterministic plan.
2. Strict target identity/provenance and Vault checkout preflight; collision handling; frame-specific dependency checks.
3. Explicit opt-in transactional mutation with per-file journal/backups, failure handling, compensating rollback and reopen verification.
4. Retain and verify profiler timing of stages, failures, total elapsed and baseline comparison.
5. Static compile-oriented review and executable fixture tests; MU Inventor 2025 disposable-model validation separately.

**No release readiness claim. Do not notify MU as completed candidate.**
