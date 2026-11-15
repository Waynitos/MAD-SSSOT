# PROPERTY REFRESH TEST 01 — verified source extraction and next test gate (2026-11-16)

**Scope:** only `feature/sweeper-v2.2.34-existing-target-repair`. **Status:** source-inspected, NOT Inventor-tested, NOT a complete APPLY candidate.

## Evidence from Friday rule (blob `5279780a5ee5512a8e740f4884f957a57781c58b`)
Source: `scripts/ilogic/experiments/BBn_PROPERTY_REFRESH_ONLY_PWTP_01.iLogicVb`.

- Lines 95 onward: `UpdateProp` retrieves `Inventor.Property` via `PropertySet.Item(name)`, compares `.Value`, and assigns `p.Value = value` only when `apply` is true. Its catch is unqualified and hides the COM failure.
- Lines 114 onward: `UpdateLeadingPJ` reads the property and uses `^PJ[0-9]{5}(?=-)` to replace **only** the leading project token; suffix is preserved. It calls `UpdateProp`.
- Lines 20–21: file enumeration is top-level only, not assembly dependency traversal.
- Lines 44–50: drawing routine sets `DRAWING_NUMBER` to filename-derived `name`, and resets `REVISION`, Design Tracking `Revision Number`, `DRAWN`, `1st REV`, `1st REV BY`, `1st REV DESCRIPTION`. **Do not reuse this drawing routine unchanged.** Exact title-block field mapping requires drawing/template evidence.
- Lines 54–60: model property writes are conditional on `CS_CopyProject` provenance; otherwise eligible older models can be skipped.

## Mandatory next diagnostic, no implementation invention
1. **Single model file:** instrument the **same** `UpdateProp` and `UpdateLeadingPJ` functions, changing only exception reporting (record `ex.ToString()`) and readback diagnostics, with no altered prefix logic. Test Part Number and SPECIFICATION on a backed-up checked-out file.
2. **Single drawing:** inspect actual title-block field references and current iProperties before selecting any drawing property setter. Avoid all Friday revision resets.
3. **Then** use a single shared core called unchanged by the assembly and drawing wrappers. A wrapper must not duplicate prefix replacement or property setters.
4. Only after runtime proof, expand to GA `AllReferencedDocuments` and folder drawings. Distinguish paths inside project root from external CC/JC/SJD roots; name prefixes alone are not library classification.
5. APPLY requires explicit confirmation, Vault/read-only/dirty safeguards, per-file error logging and post-save persisted readback. Static-only checks cannot prove COM, Vault or Inventor behavior.

## Current blockers
- No host-runtime evidence proving the recovered setter on the present Inventor/Vault test environment.
- No verified mapping from target drawing title blocks to source iProperties.
- No demonstrated persisted readback after save and reopen.
- No tested fail-closed strategy for COM hangs or Vault checkout.

**Decision:** Do not promote existing preview wrappers or experimental smoke tests to a complete candidate. Do not modify production or the parallel Existing Target Repair implementation.
