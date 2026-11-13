# Property Refresh Test 01 — Qualification blocker audit (2026-11-14)

Branch: `feature/sweeper-v2.2.34-existing-target-repair`. Scope: `BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb` and its offline source contract test. **Not Inventor tested, not qualified, no integration authorized.**

## Source-level findings

The existing static test checks for the *presence of tokens*, not end-to-end execution or safety semantics. It must not be treated as proof that property changes are safe or persistent.

1. **Vault ownership not enforced — BLOCKER.** `EligibilityReason` checks only filesystem ReadOnly. Writable is not equivalent to checked out by the current user. A future APPLY-capable rule must query authoritative Vault state or require an independently confirmed, explicit checked-out file manifest; fail closed on unknown state. No automatic checkout.
2. **Disk persistence not verified — BLOCKER.** `Save2(False)` is followed by reads from the same live `doc.PropertySets`. This does not establish what was persisted. Require close/reopen or independent disk-side validation before reporting VERIFIED. In-memory validation may be logged as a distinct intermediate state.
3. **Wrong scope for multi-folder projects — BLOCKER.** Root is `Path.GetDirectoryName(active.FullFileName)`, and `EligibilityReason` rejects everything outside that directory tree. Valid sibling `Non Std Parts` and other project folders can be omitted. Require an explicitly trusted old/new project root and path normalization; classify external CC/JC/SJD libraries by resolved roots, not names. Do not weaken the containment gate to solve this.
4. **Partial writes lack recovery — BLOCKER.** Properties are assigned one by one; if an assignment or save fails, the open document may remain dirty with partially updated values. The `Finally` block deliberately does not close a dirty document. Record original values, stage an entire file's mutation, provide rollback/restore or explicit recovery quarantine, and report exact partial status.
5. **Core is not yet independently reusable — BLOCKER.** `Sub Main` contains discovery, prompt flow, file lifecycle and mutation sequencing. Helpers are embedded in the same rule and use log/path parameters. Extract one canonical core implementation with a narrow adapter and separate test harness, rather than copying its body.
6. **No bounded COM execution — BLOCKER.** `AllReferencedDocuments`, `Documents.Open`, `Save2` and `Close` are synchronous. Stopwatch measurements help diagnosis but do not interrupt hung Inventor COM. Design a cooperative per-file checkpoint/recovery strategy and document limits of any watchdog.
7. **Drawing mapping evidence incomplete — HOLD.** Only existing `DRAWING_NUMBER` is touched, conservatively. Do not extend to revision/author/issue fields until verified against a proven prior rule and explicitly approved. Existing drawing revision values must remain untouched.
8. **Structured changes and outcomes absent — HOLD.** Changes are encoded as tab-delimited strings, making audit and rollback harder. Use typed change records: path, property-set ID/name, property, original, proposed, applied, verified, failure reason; distinguish PREVIEW, SAVED, DISK_VERIFIED, SKIPPED and FAILED.
9. **Counts misleading — HOLD.** `modified` increments even in DRY RUN and is labelled candidate-or-verified; it does not distinguish actual file writes from preview candidates. Separate counters.
10. **Inventor compatibility unproven — BLOCKER.** Validate iLogic compilation, API signatures and behavior on target Inventor versions using disposable checked-out copies; specifically verify `ItemByName`, `Close(True)`, `Save2(False)` and drawing property sets.

## Strict static gate results

A source inspection on 2026-11-14 looked for explicit Vault ownership validation, independent disk reopen verification, named project root handling, typed change records, separate discovery routine, elapsed-time instrumentation, COM timeout/cancellation mechanism and recovery logic. **0 of 8 capabilities are evidenced in the candidate source.** These are qualification gaps, not proof the code will fail in Inventor. The original contract script may still report passes because it tests weaker predicates.

## Minimum safe next implementation sequence

1. Introduce versioned core interfaces: `DiscoverCandidates(request)`, `ClassifyEligibility(file, roots, vaultState)`, `PlanPropertyChanges(file, prefix, mapping)`, `ApplyAndVerify(file, plan)`, `RecordOutcome(outcome)`. Define contracts and failure modes before implementing.
2. First deliver read-only dry-run with robust project-root and library classification, typed changes and logs. Verify assembly and drawing discovery on nested disposable project data.
3. Add Vault-ownership-aware APPLY, atomic-per-file recovery policy and disk readback. Explicitly fail closed where ownership cannot be established.
4. Add regression tests for nested/sibling folders, in-project JC/SJD copies, external CC/JC/SJD roots, read-only/dirty/locked files, missing properties, prefix edge cases, duplicate references, save failures, partial mutation and repeat idempotency.
5. Only after actual Inventor tests and evidence promote core to the shared BEEXCITED function library; the standalone wrapper and future Clean Sweeper adapter must call the same implementation.

**Status:** Work in progress. Do not announce readiness or run APPLY on production files. Existing Target Repair remains separate. No production/main changes are authorized.
