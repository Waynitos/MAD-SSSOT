# PROPERTY REFRESH TEST 01 — qualification matrix (draft, 2026-11-17)

Scope: `feature/sweeper-v2.2.34-existing-target-repair` only. This document is a safety gate, **not** Inventor runtime qualification. Do not merge or enable APPLY from this document.

## Shared function contracts

| Component | Input | Output | Failure | Status |
|---|---|---|---|---|
| Discovery v0.1.0-preview | Saved active AssemblyDocument or drawing path | Unique .iam/.ipt references (including GA) or active plus sibling .idw/.dwg | Throw on missing/unsaved/COM errors; discard partial result | Shared source exists; Inventor not validated |
| Pure prefix planner | Existing property value and validated PJ##### target | Change record preserving suffix after leading PJ#####- | Reject invalid target; no change if no eligible prefix | Existing module; review executable tests |
| Root classification | Canonical project root and external protected roots | Eligible/protected with reason | Fail closed on ambiguous roots, junctions, Vault state | Separate classifier exists; not wired into preview |
| Snapshot readback v0.1.0-preview | Saved open Inventor document, property set/name | Current in-memory property value | Throw on missing/null/unreadable property | Shared source exists; not disk verification |
| Mutation engine | Approved immutable plan + checked-out ownership proof + clean document | Per-property result and persisted verification | Abort before first write if any preflight fails; record partial write and stop | NOT IMPLEMENTED |
| Per-file audit logger | Run ID, file, before/after, reason, verification state | Append-only structured record | Logging failure must prevent APPLY or halt further writes | NOT EXTRACTED |
| GA standalone wrapper | Active GA .iam + PJ##### + explicit mode | Plan and audit; APPLY only after gate | Fail closed | DRY RUN only |
| Drawing standalone wrapper | Active GA .idw/.dwg + PJ##### + verified title-block mapping | Plan and audit | Unverified mapping must block APPLY | DRY RUN hypothesis only |
| Future Clean Sweeper adapter | Same shared engine API, no rewritten mutation logic | Identical engine results | No Copy Design dependency | NOT IMPLEMENTED |

## Mandatory APPLY gates

1. Explicit dry-run default, separate typed APPLY, and complete immutable preflight plan; never infer permission from file writability.
2. Confirm Vault checkout ownership using authoritative Vault state, not file attributes or directory membership. Refuse missing, unknown or foreign checkout.
3. Protect external Content Center, JC and SJD library roots before filename heuristics. JC/SJD names inside approved old-project roots remain eligible only after Vault ownership verification.
4. Reject dirty documents, unresolved references, unsaved files, inaccessible logs and ambiguous root boundaries. Avoid silently closing user documents or saving unrelated changes.
5. Mutate only Design Tracking Part Number and existing custom SPECIFICATION leading PJ prefix, plus individually documented and approved populated fields. Preserve suffix, type, revision and all unrelated properties.
6. For drawings, independently establish property-to-title-block mapping from real drawing definitions and field expressions; do not assume DRAWING_NUMBER.
7. Save only approved changed files, reopen from disk and compare exact expected values. In-memory snapshots do not satisfy persisted readback.
8. Log before/after values, identity, classification, ownership proof, save and reopen outcomes for each file. On partial failure stop subsequent writes, report exactly which files may have changed, and require recovery rather than claiming rollback.
9. COM calls may hang; catchable exceptions are not a timeout. Specify host isolation/watchdog and recovery procedure before unattended APPLY.
10. No source-file changes outside the selected branch; keep Existing Target Repair separate. Never claim Inventor/Vault validation from static tests.

## Regression scenarios (must be executable before qualification)

- Valid PJ prefix with suffix; same target; missing prefix; malformed PJ; embedded PJ; mixed-case prefix; empty/null property.
- Nested GA with repeated references, missing/unsaved submodel, subassembly outside GA folder but inside approved project root, external protected library, project-local JC/SJD, path boundary and junction/symlink escape.
- Drawing active plus sibling IDW/DWG, unrelated drawings, missing property, mapped versus unmapped title-block fields, revision unchanged.
- Read-only file, foreign Vault checkout, unknown Vault state, dirty already-open document, logging failure, save failure, reopen mismatch, partial write, COM failure/hang.
- Verify no duplicated mutation implementation between standalone and integration adapter; preview contains no property writes or Save2.

## Observed static limitations

Current preview derives its eligible root from the active document folder and uses embedded `EligibilityReason` and `WriteLine`, so shared root classification and logging are not integrated. The preview explicitly blocks APPLY. `BEEXCITED_PropertyRefreshReadback` reads open-document memory only. Drawing mapping is unverified. These are source-level observations, not executed Inventor tests.

**Qualification:** INCOMPLETE. No APPLY, no production merge, no runtime-validity claim.
