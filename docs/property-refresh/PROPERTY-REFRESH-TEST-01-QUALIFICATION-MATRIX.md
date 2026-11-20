# PROPERTY REFRESH TEST 01 — qualification matrix (draft)

Status: **STATIC SPECIFICATION ONLY — NOT QUALIFIED FOR APPLY**. Scope: `feature/sweeper-v2.2.34-existing-target-repair` only. No Inventor/Vault runtime validation. Existing Target Repair is a separate workstream.

## Reuse invariant
The same shared functions must be called by standalone assembly and drawing wrappers and by the future Clean Sweeper adapter. No Copy Design dependency, no copied implementation, and no UI prompts inside discovery, eligibility, planning, mutation/readback or logging modules.

## Current proven-by-inspection baseline
`BEEXCITED_PropertyRefreshPure.iLogicVb` v0.1.0-preview exports `NormalizeProjectPrefix`, `ReplaceLeadingProjectPrefix`, `PlanDrawingNumber`, `PlanExistingModelProperty` and `PlanExistingDrawingProperty`. The module has no Inventor calls, UI or writes. **Not compilation tested**. Its drawing planner assumes custom `Inventor User Defined Properties / DRAWING_NUMBER`; that mapping is not approved or verified. Do not enable APPLY from this assumption.

## Contract and acceptance matrix

| Component | Inputs | Output | Fail closed / safety | Minimum regression |
| --- | --- | --- | --- | --- |
| Pure prefix planner | existing string; exactly PJ##### target | unchanged or suffix-preserving planned value | malformed target raises error; absent leading PJ#####- stays unchanged | lower/upper-case prefix, malformed target, null, empty, embedded PJ, repeated prefix, Unicode suffix |
| Assembly discovery | active saved .iam, approved project root | de-duplicated nested reference inventory with source path and document type | missing refs, unresolved refs, cycles, inaccessible paths and document errors logged; never mutate | deep nesting, shared refs, cycles, missing files, Content Center refs |
| Library eligibility | canonical resolved path, old project root, external protected roots | allow/deny with reason | reject unknown roots, external CC/JC/SJD, symlinks/junction/UNC aliases without identity resolution, read-only and non-owned Vault files | JC/SJD *inside* project root allowed if eligible; same name *outside* denied; traversal escapes denied |
| Model plan | approved eligible model + current property values | list of property changes | only Part Number, SPECIFICATION and separately approved populated project fields; never create absent fields by default | unchanged value, absent field, non-string, empty field, suffix preserved |
| Drawing discovery | active saved .idw/.dwg and folder | active + sibling drawings, deterministic order | exclude other folders, unsupported documents, unsaved drawings | mixed IDW/DWG, duplicate, read-only, inaccessible sibling |
| Drawing plan | verified property mapping and filename/property identity | explicit property changes | unverified mapping blocks APPLY; no arbitrary revision resets | mismatched prefix, absent mapping, revision untouched, suffix preserved |
| Guarded mutation | approved plan, explicit APPLY, Vault ownership, clean document, writable file | per-file outcome | default dry-run; abort on dirty/locked/readonly/Vault conflict; preserve source files | no-op preview, blocked APPLY, partial failure, interrupted save |
| Persisted readback | saved file reopened independently and expected plan | pass/fail per property | in-memory readback is insufficient; failures prevent success | stale cache, save error, property mismatch, reopening error |
| Logging | run ID, file path, decision, before/after, error | append-only per-file record | redact secrets; log attempted and actual writes separately | crash/interruption, denied files, no-write preview, failed readback |
| Standalone wrappers | active GA document + target prompt | preview and gated APPLY result | UI-only; invoke shared functions unchanged | no Copy Design reference; unsupported active doc rejected |
| Future integration adapter | same contracts as wrappers | invocation of same shared library | no separate algorithm | source-level identity check of invoked functions |

## Release gates
1. Verify real Inventor drawing iProperty mapping using representative known-good drawings; explicitly approve fields.
2. Implement and statically qualify canonical path/ownership/dirty-document/COM timeout and recovery gates; fail closed on unknown.
3. Ensure post-save *disk-persisted* readback and per-file failure isolation.
4. Execute regression suite and record exact commands, environment, pass/fail counts and limitations; static tests do not imply Inventor compatibility.
5. Keep APPLY disabled until those gates pass. Commit a complete candidate only to the designated feature branch and report Inventor runtime testing as still required.
