# BEEXCITED SQL Database — Batch Property Editor (Future-State Roadmap)

Status: PROPOSED / NOT IMPLEMENTED
Added: 2026-11-13
Scope: Future database-backed Inventor/Vault tooling; not a dependency of standalone Property Refresh Test 01.

## Vision
Provide a GUI comparable to Autodesk Vault's Ctrl+E multi-file property editor and Copy Design's editable file grid, with direct file discovery, filtering, bulk selection, review and controlled batch updates. Support one or many files, including assembly hierarchies, drawing folders and arbitrary database query results. Support both interactive edits and automated jobs.

## Requirements
1. Search/filter/select individual files, arbitrary sets, saved selections, folder contents, entire recursive assembly references and related drawings; show source, target, lifecycle and Vault status.
2. Editable grid: file rows; configurable property columns; mixed-value indicators; per-file overrides; bulk set/replace/prefix substitution/clear where allowed; show original, proposed and effective values; preview and validation before APPLY.
3. Property schema registry: Design Tracking Part Number, custom SPECIFICATION, approved project fields and configurable property mappings; distinguish iProperties from Vault UDPs and database metadata; never assume all are synchronized automatically.
4. SQL stores indexed metadata, selection sets, proposed change sets, job state, audit history, source hashes/timestamps, and post-write verified values. SQL is not itself the authoritative writer of Inventor iProperties.
5. Execution adapter uses the reusable, versioned Property Refresh core library. Perform Inventor API updates where necessary; use Vault-supported APIs/workflows for Vault properties and file management. No direct edits to Vault database.
6. Vault-controlled files: preflight current checkout/ownership/permissions and lifecycle restrictions. Explicitly request or perform authorized checkout when permitted; otherwise queue/skip and report. Commit/save and check in only per approved workflow. Non-Vault files: check write access, locking, dirty state and version.
7. Dry-run first; conflict detection, idempotent updates, per-file transactions or compensating recovery, retries, bounded concurrency, cancellation, progress, detailed per-file logs and post-save readback verification. Partial failures must be visible and recoverable.
8. Protect external Content Center, JC, SJD and other library roots; classify by actual resolved path and project ownership rather than filename alone. Source and target roots must be explicit.
9. Support batch automation through rules/jobs/schedules with approval gates and scoped access; no silent updates of unapproved files.
10. UI concepts: Vault-like file grid, property columns, filters, multi-select, batch edit pane, before/after diff, preview, apply, results, audit trail and retry failed items.

## Delivery phases
- Phase 0 (now): complete standalone Property Refresh Test 01 (active GA recursive model traversal; active GA drawing + same-folder drawings). Prove core function and regression suite independent of Copy Design.
- Phase 1: extract stable shared functions and documented interfaces for discovery, property mapping, safety, execution, logging and verification.
- Phase 2: design SQL schema and index/sync mechanism; prove read-only catalog and selection/query workflows.
- Phase 3: implement read-only batch property editor prototype with preview/diff, using indexed files and resolved Vault state.
- Phase 4: controlled write pilot on checked-out test files, audit, verification, recovery and Vault API workflow.
- Phase 5: production-grade multi-file automation, permission/approval controls, saved batch jobs and scheduling.

## Acceptance criteria
- A user can select one or many arbitrary eligible files and preview exact changes before execution.
- A selected batch can update properties without copying or renaming any file.
- External protected libraries and non-owned files cannot be silently changed.
- Vault-controlled files are not written without required authorization/checkout.
- Every attempted write has a result, audit record, and verified file-side value or explicit failure.
- The same tested Property Refresh implementation is used by standalone iLogic, Clean Sweeper and the future SQL batch editor.

This is a future-state plan, not an implementation claim.