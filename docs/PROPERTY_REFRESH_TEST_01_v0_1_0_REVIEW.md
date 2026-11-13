# Property Refresh Test 01 — v0.1.0 static assessment

Status: COMMITTED CANDIDATE; NOT INVENTOR-TESTED; NOT APPROVED FOR REUSE.
Branch: feature/sweeper-v2.2.34-existing-target-repair
Rule: scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb

## Comparison with previous experiment
The previous BBn_PROPERTY_REFRESH_ONLY_PWTP_01.iLogicVb scanned a prompted folder's top level only, skipped JC-named files irrespective of actual location, required CS_CopyProject on models, and reset multiple drawing revision/author/issue properties. This new experiment uses active-document context, recursively enumerates model references via AllReferencedDocuments, scopes edits to the GA's folder tree, and does not reset revisions.

## Static source inspection (not compilation)
- Validates active saved .iam/.idw/.dwg, PJ##### prefix and explicit APPLY.
- Aborts if active document has unsaved edits.
- Assembly: active GA plus referenced IAM/IPT files; drawing: active GA drawing plus IDW/DWG files in same folder.
- Deduplicates by case-insensitive full path.
- Rejects paths outside active GA's folder tree, missing files and readonly files; does not classify by JC/SJD filename. External Content Center/JC/SJD roots outside project tree are excluded.
- Changes only existing leading PJ#####- prefixes in model Part Number and SPECIFICATION, and existing DRAWING_NUMBER leading prefix on drawings. No revision resets, no SaveAs/rename/reference operations.
- Logs before/after, failures, skips and in-memory readback after Save2(False).
- Uses one implementation for both preview and APPLY; no Copy Design dependency.

## Known limitations / blockers before qualification
1. Inventor/iLogic compilation and runtime are NOT verified. Test with Inventor 2025 in disposable checked-out copies; check compatibility with Inventor 2017 separately.
2. The document path root is the active GA's immediate folder. Referenced project parts in sibling folders are deliberately excluded; future work must derive the trusted project root explicitly and protect external library roots.
3. Path scoping is not a Vault checkout/ownership check. A writable file may still be Vault-managed or not owned by the user. APPLY must be used only on known checked-out disposable test files.
4. Document references may already be loaded and dirty; such documents are skipped. The Inventor COM traversal/open/save calls are synchronous; there is no reliable timeout or cancellation yet.
5. Post-save readback is from the open Inventor document, not a close/reopen disk verification. Dirty state after a partial write/save failure may remain; no rollback implemented.
6. Drawing mapping is intentionally conservative. DRAWING_NUMBER updates only if it already has leading PJ#####-; other drawing fields require verified prior-rule evidence and approval.
7. No proven automatic Vault checkout, no full SQL editor, no GUI batch property editor. The future SQL roadmap remains separate.
8. No verified static compiler/test runner was executed. The inspection is manual source review, not a passed automated test suite.
9. The core helpers remain within a single rule, not yet an externally callable compiled function library. Extracting a reusable shared source without duplicating logic is a future qualification step.
10. A model without a leading PJ#####- property is unchanged by design; this avoids overwriting arbitrary metadata.

## Proposed manual acceptance tests
- Dry-run on nested assembly with at least two levels of IAM/IPT; compare candidate count to referenced documents.
- Confirm original external JC/SJD/Content Center files are skipped; confirm in-project JC/SJD-named target copies can be updated.
- Test missing custom SPECIFICATION, unchanged prefix, mixed case, no-hyphen, readonly file, and dirty active doc.
- Test GA drawing plus other IDW/DWG in same folder, including revision fields: revision must remain unchanged.
- APPLY only on backed-up checked-out disposable target files; verify property values by reopening, verify original source untouched.
- Repeat APPLY to establish idempotency; review log and investigate any dirty-document/save failures.

Do not integrate this candidate into Clean Sweeper until compilation, Inventor execution, post-save disk verification and regression acceptance pass.
