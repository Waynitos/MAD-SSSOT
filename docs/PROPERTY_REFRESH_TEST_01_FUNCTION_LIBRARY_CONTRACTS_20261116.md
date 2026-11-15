# PROPERTY REFRESH TEST 01 — function-library contracts and acceptance gates
Status: DESIGN CONTRACT / NOT QUALIFIED FOR APPLY
Branch: feature/sweeper-v2.2.34-existing-target-repair
Version: contract 0.1.0 (2026-11-16)
Compatibility target: Inventor 2017 iLogic/VB.NET; confirm API availability against installed host before runtime use.

## Architecture and reuse invariant
One shared implementation of each function. The standalone .iam and .idw/.dwg entry rules and later Clean Sweeper integration adapter call the exact same shared functions; adapters may only supply inputs and display results. No Copy Design dependency, no source-file rename/copy, no edits to Existing Target Repair. UI is outside core. Source must compile and execute in the target iLogic environment before qualification; no such validation is claimed here.

## Contract A: Prefix planner (pure)
Input: old string, target PJ#####. Output: unchanged/skipped or planned new string and reason. Match only leading `^PJ[0-9]{5}(?=-)`; retain all bytes after five digits. Do not rewrite internal PJ tokens or blank fields. Failure: invalid target, null value, nonmatching prefix. Tests: PJ00123-A -> PJ00999-A, PJ00123-A-B -> PJ00999-A-B, embedded PJ unchanged, empty unchanged, target already present no-op. Reuse existing `UpdateLeadingPJ` pattern; don't implement an alternative without evidence.

## Contract B: GA discovery (read-only)
Input: active saved .iam, Inventor application, optional project root. Output: deterministic deduplicated full-path set including root and nested referenced .iam/.ipt models, plus unresolved/error records. Prefer `AllReferencedDocuments` with documented traversal/coverage and preserve path identity; do not use folder scans as substitute for references. Failures: unsaved root, unresolved reference, inaccessible path, COM exception, non-model reference. Never mutate or save during discovery. Tests: deep nesting, repeated occurrence, cycles/duplicates, missing links, outside-root dependency, nested JC/SJD in project root.

## Contract C: Drawing discovery (read-only)
Input: active saved .idw/.dwg. Output: active drawing plus eligible .idw/.dwg files directly in same folder, canonicalized and deduplicated. Exclude unrelated extensions and subfolders unless later explicitly approved. Failures: unsaved drawing, inaccessible folder, corrupt/unsupported document, non-Inventor DWG. No drawing field writes until actual title-block reference/property mapping has been inspected in the user's proven rule and verified on a disposable drawing.

## Contract D: Library protection (pure classification)
Input: canonical file path, old project root, configured Content Center and JC/SJD external roots, file provenance, writable/Vault state. Output: ALLOW, SKIP_PROTECTED, SKIP_READONLY, SKIP_OUTSIDE_SCOPE, or REVIEW_REQUIRED with reason and matched root. External protected roots override filename patterns; JC/SJD filenames inside old project root may be eligible. Unknown provenance is REVIEW_REQUIRED, not blanket allow. Do not infer ownership from filename alone. Tests: external CC, external JC, external SJD, project-local JC/SJD, boundary-prefix path (e.g. C:\\Project vs C:\\Project2), case-insensitive Windows paths, symlink/junction if applicable.

## Contract E: Property mutation and persisted readback (side-effecting)
Input: eligible open Inventor.Document, approved property mapping, planned old/new pairs, explicit APPLY token, preflight snapshot. Output: per-field old/planned/assigned/in-memory/persisted values, save status and detailed failure. Default DRY RUN: no assignment, save, dirty-state change or source-file write. In APPLY, check checkout/read-only/Vault, pre-existing dirty state, document identity, required property sets, and explicit field approval before mutation. Reuse the recovered direct `Property.Value = value` setter; capture exact COM exception/HRESULT instead of swallowing. Part Number: Design Tracking Properties; SPECIFICATION: Inventor User Defined Properties. Only nonblank approved project fields with verified mapping. No revision/issue/reset fields. Save only changed eligible documents; verify after save by reopening or independently reloading a safe copy, not merely rereading in-memory property values. A failed readback is a failed test, never success. Define abort/rollback and recovery protocol before enabling APPLY. No unbounded COM retry: elapsed-time checkpoints and user-visible host recovery instructions; an in-process iLogic rule cannot reliably kill a hung COM call.

## Contract F: Audit logging (side-effect only to separate log)
Input: operation id, timestamp, mode, root, target, each discovered path, classification, property changes, exception, save/readback. Output: append-only UTF-8 CSV/JSONL log outside protected source tree with stable schema/version and deterministic ordering. Log skipped files and no-ops as well as changes; redact unnecessary private paths when sharing. Logging failure must not silently continue APPLY.

## Contract G: Entry workflows and adapters
IAM standalone: validate active .iam; prompt target PJ#####; run A/B/D then preview; explicit APPLY after reviewed counts; E/F only on approved eligible files. Drawing standalone: validate active .idw/.dwg; prompt target; C/D; verify drawing mapping; preview; explicit APPLY; E/F. Both invoke shared library unchanged. Future Clean Sweeper adapter invokes same library without adding property setters or discovery copies. UI prompts and dialogs only in entry workflows. No adapter implementation before property test is complete.

## Minimum qualification matrix
1. Static checks: exact source provenance, shared-call identity, no duplicated setters, no SaveAs/Copy Design, dry-run default, explicit APPLY gate, no revision writes, root-boundary classification, version and documented contracts.
2. Pure unit tests: prefix planner and library classifier with adversarial Windows path cases.
3. Mock tests: traversal/dedup/error propagation, logs, dirty/read-only guards, mapping whitelist, save/readback failures.
4. Inventor 2017 disposable files: one checked-out model dry-run -> APPLY -> close/reopen readback; one drawing field mapping verified -> dry-run -> APPLY -> close/reopen readback; nested GA and drawing folder smoke tests.
5. Vault regression: protected libraries unchanged, checkout/lock respected, dirty documents not overwritten, COM failures surfaced, source files unchanged in DRY RUN.
6. Integration gate: adapters reference identical shared library version/hash; no implementation fork; Existing Target Repair stays separate.

## Current blockers
The actual drawing title-block property mapping is unverified; APPLY is not qualified; persisted post-save readback, host/Vault runtime tests, VB compilation, and shared library integration are outstanding. The previous Friday rule contains folder-only discovery, CS_CopyProject gating and revision resets, which must not be copied forward. Existing static gate was committed but its execution has not been demonstrated.
