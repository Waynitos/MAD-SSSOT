# PROPERTY REFRESH TEST 01 — APPLY gate contract (2026-11-22)

Status: **DESIGN CONTRACT ONLY — NOT QUALIFIED FOR APPLY**. Scope: property refresh only. No Copy Design dependency. No Inventor runtime validation. Do not alter production or Existing Target Repair logic.

## Source baseline inspected
- `scripts/ilogic/experiments/BEEXCITED_PropertyRefreshPure.iLogicVb` (blob c2c43385ecf5f70ac903b3690080eaaf20469b52): five planning functions; preserve unchanged.
- `scripts/ilogic/experiments/BEEXCITED_PropertyRefreshDiscovery.iLogicVb` (blob 6017a955b55aee246f77873a7387e303c328ac75): recursive referenced-model enumeration, same-folder drawing enumeration; preserve unchanged pending test.
- `scripts/ilogic/experiments/BEEXCITED_PropertyRefreshEligibility.iLogicVb` (blob 3d88cfb4c08472355b7c9cda3971daa59a705cfa): lexical preview classification only; never interpret preview candidate as APPLY authorization.

## Non-negotiable architecture
One shared, versioned implementation per operation, called UNCHANGED by independent assembly wrapper, drawing wrapper, static/offline harness where feasible, and future Clean Sweeper adapter. Wrappers may gather input and display results but may not implement prefix replacement, traversal, classification, property writes, or readback themselves. Pure planner remains independent of Inventor, UI and Copy Design.

## Proposed guarded operation contract
Input: saved active Inventor document (.iam or .idw/.dwg), exactly PJ##### target, approved canonical project root, approved and protected canonical root sets, explicit mode DRY_RUN or APPLY, verified per-property mapping, preflight snapshot, Vault ownership evidence, approved populated fields list.
Output: immutable per-file change plan and audit records with file identity, previous value, proposed value, decision, reason, operation outcome, and persisted-readback outcome.
Failure: fail closed on invalid target, missing/ambiguous property mapping, path alias or reparse-point ambiguity, protected external library, outside-root file, read-only file, Vault checkout/ownership uncertainty, dirty document, unsaved document, stale plan, COM timeout/hang, save error, or readback mismatch. A partial write is a failed run requiring recovery; never mark success based on in-memory values alone.

### APPLY gate
1. DRY_RUN default; APPLY only after a separate explicit confirmation against a displayed immutable plan.
2. Re-resolve each candidate's *physical* file identity and root ownership immediately before write. Lexical prefix matching is insufficient; reject unresolved junctions, symlinks, UNC aliases and case/normalization ambiguities. Protect external Content Center/JC/SJD roots regardless of filename. JC/SJD-named files *inside* the approved old project root may remain eligible.
3. Validate Vault ownership/checkout, filesystem write access and current dirty/unsaved state. No automatic checkout, save of pre-existing dirty edits, or source file mutation.
4. Verify every property set/name/type and original value against the preview snapshot before writing. No implicit creation of missing fields; only explicitly approved populated project fields. For drawings, do not write DRAWING_NUMBER until mapping is verified against actual drawings; never reset revisions.
5. Save only files modified by this run. Persisted readback must use a fresh disk-backed document after safe close/reopen or equivalent independently verified disk read, not the same open document. Compare every changed field. Log failures per file and stop/contain further mutation on uncertainty.
6. Treat Inventor COM hangs as an externally supervised timeout/cancellation condition; do not claim that synchronous in-process COM calls can be forcibly timed out safely.

## Standalone workflow contracts
**Assembly:** saved active GA .iam; discover root plus nested referenced .iam/.ipt once; plan Design Tracking Properties/Part Number and custom SPECIFICATION only when leading PJ#####- exists, preserving full suffix. Additional project fields require explicit approved populated mapping. External libraries blocked.

**Drawing:** saved active GA .idw/.dwg; discover active drawing plus .idw/.dwg in same directory; plan only independently verified property mappings with filename/property identity agreement. Do not infer drawing property mapping or modify revision fields.

## Minimum executable regression matrix (not yet executed)
- Target validation: valid PJ00001, invalid short/long/non-numeric/missing.
- Prefix: preserve complete suffix; malformed, embedded, empty, unchanged values untouched.
- Discovery: nested references, duplicates, unsaved refs, COM error, inaccessible drawing folder, mixed .idw/.dwg.
- Protection: external Content Center/JC/SJD excluded; JC/SJD filenames within approved project root allowed; symlink/junction/UNC alias denied when physical identity unresolved.
- Preflight: read-only, Vault unchecked-out, dirty, unsaved, stale property snapshot and missing property mapping all deny APPLY.
- Mutation: DRY_RUN makes zero writes; explicit APPLY requires complete preflight; mid-run failure produces audit and never false success.
- Readback: open-document echo insufficient; persisted mismatch fails qualification.
- Drawing: filename/property identity mismatch denied; no arbitrary revision changes.
- Reuse: wrappers and adapter reference shared functions; no duplicated prefix or property-write implementations.
- Compatibility: static syntax/build against declared VB/iLogic target, then separate Inventor 2017 and target production-version runtime tests.

## Verification record
2026-11-22: Three source modules retrieved and read through GitHub connector; this is **source inspection only**, not compilation, executable static testing, Inventor testing, or APPLY qualification. All gates remain blocked pending implementation and test evidence.
