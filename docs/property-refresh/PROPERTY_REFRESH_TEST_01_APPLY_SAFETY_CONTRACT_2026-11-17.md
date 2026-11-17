# PROPERTY REFRESH TEST 01 — APPLY safety contract (draft, 2026-11-17)

Status: **NOT QUALIFIED — APPLY BLOCKED**. Scope: isolated feature branch only. No Copy Design, source-file edits, Vault checkout, or production changes.

## Reusable function contracts

| Module | Inputs | Output | Failure / guard |
|---|---|---|---|
| Discovery | Active saved GA assembly or drawing | Deduplicated full paths: assembly + nested .iam/.ipt, or active drawing + sibling .idw/.dwg | Abort on Inventor traversal/IO failure; no writes |
| Path identity / eligibility | Candidate, approved old-project roots, explicit protected Content Center/JC/SJD roots, resolved filesystem identity | Eligible/blocked decision with reason | **Fail closed** on symlinks, junctions, UNC aliases, inaccessible paths, unverified identity, protected roots, read-only files. Filename JC/SJD alone does not block project-local parts |
| Pure property planner | Existing string, validated PJ##### target, approved mapping | Old/new value preserving suffix, or no-op/rejection | Never rewrite non-leading PJ text; no blank/new property creation without approval |
| Mutation (future, NOT IMPLEMENTED) | Explicit APPLY, approved per-file plan, authoritative Vault checkout ownership, clean document, recoverable preimage | Per-property write results | Abort before any write if any precondition fails; detect partial writes and require recovery; no revision resets |
| Readback | Property set/name, expected value, reopened persisted file | Observed value and verified/unverified result | In-memory snapshot is **not** persisted verification; reopen after save; abort on mismatch |
| Audit | Run ID, file, old/new, decision, error, verification status | Durable per-file audit record | Audit write failure blocks APPLY; do not claim verified without persisted readback |
| UI wrappers | Active .iam or .idw/.dwg, PJ##### prompt, explicit APPLY | Calls the **same shared functions unchanged** | Dry-run default; no duplicate traversal, planning or mutation code |
| Integration adapter (future) | Clean Sweeper context + same core contracts | Calls shared library unchanged | No Copy Design dependency in shared core |

## Mandatory gates before implementing APPLY

1. Retrieve and compare previously **successful** iLogic property-refresh rules and external examples; document exact API/property-set mappings and compatibility with Inventor 2017 and 2025. Do not assume DRAWING_NUMBER is correct.
2. Prove canonical filesystem identity and protected-root precedence against junction/symlink/UNC aliases; reject unresolved identities.
3. Verify actual Vault ownership/checkout and read-only state for **every** target, including all nested references. Detect pre-existing dirty documents and do not save unrelated edits.
4. Confirm Design Tracking **Part Number** and custom **SPECIFICATION** mapping, leading-PJ-only suffix preservation, plus an explicit allowlist of other populated project fields. Confirm drawing title-block source and revision-preserving mapping independently.
5. Implement shared, idempotent mutation and persisted post-save readback with per-file audit and partial-write recovery. Do not infer success from in-memory values.
6. Run static regression tests (including negative safety cases), VB compile checks and disposable Inventor/Vault runtime tests. Record tested/verified separately; static checks cannot establish runtime safety.

## Evidence and limitations

As inspected on 2026-11-17, `BEEXCITED_PropertyRefreshEligibility.iLogicVb` explicitly uses lexical paths, and `BEEXCITED_PropertyRefreshReadback.iLogicVb` explicitly reads only in-memory `Document.PropertySets`. The standalone `BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb` blocks APPLY and previews the unverified custom `DRAWING_NUMBER` mapping. None of these establish safe mutation or persisted verification. Existing Target Repair remains a separate parallel workstream.

Acceptance criterion: only a committed, static-checked candidate with shared core, independent wrappers and adapters, safety gates, and explicit remaining Inventor test requirement may be reported as ready for testing; **never** report Inventor runtime validation without actual Inventor execution.
