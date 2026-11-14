# PWTP-PROP-02 — crash recovery audit (2026-11-14)
Status: IMPLEMENTED pilot code / UNTESTED in Inventor / BLOCKED for full APPLY.
Baseline preserved: BBn_PROPERTY_REFRESH_ONLY_PWTP_01.iLogicVb (blob 5279780a5ee5512a8e740f4884f957a57781c58b); original Copy Sweeper v2.2.32 untouched.
Pilot: scripts/ilogic/experiments/BBn_PROPERTY_REFRESH_ONLY_PWTP_02_PILOT.iLogicVb on feature/sweeper-v2.2.34-existing-target-repair.

## Evidence
2026-11-13 DRY RUN summary scanned 411, change candidates 37, skipped 31, failed 0. User observed APPLY completion dialog then Inventor crash; 0 failures in summary is not proof of disk persistence. The actual APPLY log and Windows crash data have not been inspected.
Confirmed source defect: PadFive tests ^[0-9]{5}$ then prefixes 0; e.g. 00150 -> 000150. Fix to 1..4 digits and PadLeft(5, "0"c). Existing six-digit corruption is NOT automatically reversed; needs targeted human verification.
VB control flow: Continue For inside Try DOES execute Finally. Microsoft Try/Finally and Continue docs confirm. Not root cause.
Document lifecycle: source only calls doc.Close(True) if Not doc.Dirty. Any dirty document is left open; errors in Close are swallowed. Hidden documents also hold a reference until ReleaseReference or closure. This is a plausible cause of resource growth, not proven crash root cause.
Save2(False) saves current document only, not dependents (Autodesk documented); it is not inherently a save bug. Close(True) skips saving and discards unsaved changes (Autodesk documented). The pilot closes its own opened documents and logs dirty-discard, but does not close pre-opened docs.
JC guard previously protected exact JC+digits only. Pilot expands protection to JC+digits followed by hyphen, underscore or space. Review scope before production.
Unresolved data correctness: PROJECT NUMBER PJ00141 / RJ040 may be historical; Part Number core may not match target filename; project-specific JC derivatives may need exception review. Drawing metadata and parts-list override repair are separate.

## Pilot differences
- Desktop-only logging (abort if Desktop not available).
- Dry-run default, explicit APPLY.
- Maximum 5 eligible filenames per run, optional filename substring filter.
- Logs BEGIN, OPEN-BEGIN/END, SAVE-BEGIN/END, CLOSE-BEGIN/END, CLOSE-FAIL, RELEASE-REFERENCE.
- Skips already-open files to avoid altering user's active documents; skips dirty-on-open files.
- Close(True) for docs opened by rule, with ReleaseReference fallback on failed close; close errors counted.
- Retains original top-level folder scan and positive CS_CopyProject gate; no recursion, drawing tree traversal, rename, or Vault actions.
- This is a diagnostic pilot; source was NOT compiled or executed in Inventor by the assistant.

## MAD
AA: use existing property-set API and minimal patch; save current doc only; 5-file diagnostic to isolate lifecycle.
DA: root cause unproven; property mutations can partially apply before save; Save2/Close could trigger iLogic events or referenced-document side effects; a dry run that opens assemblies still consumes resources. Hardcoded five files may not hit candidate; use filter.
SSA: run 5-file DRY RUN, inspect desktop log and document count, then backed-up 5-file APPLY only if no lifecycle errors; reopen files and inspect properties; repeat dry run should be zero candidates for same files. Stop on OPEN/SAVE/CLOSE failure or Inventor instability. Do not run 411-file APPLY.

## External references
- Microsoft Try/Finally: https://learn.microsoft.com/en-us/dotnet/visual-basic/language-reference/statements/try-catch-finally-statement
- Microsoft Continue: https://learn.microsoft.com/en-us/dotnet/visual-basic/language-reference/statements/continue-statement
- Autodesk Save2: https://help.autodesk.com/cloudhelp/2023/ENU/Inventor-API/files/Document_Save2.htm
- Autodesk Close: https://help.autodesk.com/cloudhelp/2022/ENU/Inventor-API/files/Document_Close.htm
- Autodesk ReleaseReference: https://help.autodesk.com/cloudhelp/2022/ENU/Inventor-API/files/Document_ReleaseReference.htm
- Autodesk API training: https://blog.autodesk.io/inventor-api-training-lesson-2/

## Monday acceptance
1. Restart Inventor cleanly. Keep baseline rule untouched. Backup five local PJ00183 test files.
2. Copy pilot rule to Inventor; compile. Use same target project PJ00183 and name filter. DRY RUN; ensure desktop log shows balanced OPEN-END and CLOSE-END for each processed document and no FAIL.
3. APPLY on same backed-up files; inspect SAVE-END and CLOSE-END. If no change candidates due to filter, choose known candidate filename substring.
4. Reopen changed files in Inventor, verify SPECIFICATION, Part Number, PROJECT NUMBER, DRAWING REF/ITEM NUMBER; check for 6-digit remnants. Rerun DRY RUN; zero candidates expected for corrected fields.
5. If freeze/crash: preserve last desktop log line and Windows Event Viewer Application Error (Inventor.exe faulting module), plus Inventor version and loaded add-ins. Do not widen batch.
6. Broader 411-file test and drawings only after verified small-batch success and explicit approval.

## Sunday 2026-11-15 — additional source-audit finding

**Confirmed diagnostic defect:** PWTP-PROP-02 previously wrapped property lookup, read, and `p.Value = value` in one `Catch` returning 0, so a COM setter failure could be logged merely as `MISSING-OR-UNWRITABLE` and omitted from `failed`. This makes the prior `failed=0` metric less trustworthy as a measure of individual property writes. The original PWTP-PROP-01 has the same suppression.

**Minimal pilot-only repair:** commit `de1ce0a022e4edd5e2e3c8e2ac52bbc2a020aa5b` separates missing-property lookup from property assignment. Missing properties remain logged/skipped for compatibility. A setter failure now emits `PROPERTY-WRITE-FAIL`, rethrows to the per-file handler, and increments `failed`. No production baseline changed. Static source review only; no Inventor compilation or execution.

**Remaining risks:** the pilot's default substring filter can select five files without any change candidates; choose a known candidate and confirm `PROP` lines before APPLY. A dry run still opens models and can trigger Inventor document-load side effects; monitor `OPEN-END`/`CLOSE-END`. `changed` counts files with candidate changes before Save2 completes; never interpret it as a count of persisted files. Any partial mutation on a setter exception is discarded by `Close(True)` for pilot-opened docs, but independently triggered saves/events have not been excluded.

**Monday gate:** verify actual file backup, successful iLogic compilation, 5-file DRY RUN with candidate, 5-file APPLY with balanced lifecycle and zero FAIL, reopen saved files and inspect fields, then repeat DRY RUN. Full-folder APPLY remains BLOCKED pending workplace evidence and approval.

**Hive Knowledge Contribution:** CANDIDATE — avoid catch-all property setter error suppression in batch iLogic; provenance: PWTP-PROP-01 and PWTP-PROP-02 source, this audit, commit above. Verification: CODE_REVIEWED, not LOCALLY_TESTED or WORKPLACE_VALIDATED.
