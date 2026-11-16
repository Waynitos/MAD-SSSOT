# CLEAN SWEEPER — iLogic Function Harvest Audit BB15
Date: 2026-11-16
Status: CODE_REVIEWED (selected functions), NOT LOCALLY_TESTED, NOT WORKPLACE_VALIDATED, NOT APPROVED.
Source artifact: CLEAN_SWEEPER_PROPERTY_TEST_BB15_REVIEW_ONLY.iLogicVb (local candidate, 305027 bytes); source lineage: TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN_ENHANCEMENT_PROPERTY_TEST_FIXED (29).iLogicVb.
Related incident: https://github.com/Waynitos/MAD-SSSOT/issues/15
Purpose: record function provenance, dependencies, tests, known failures and reuse eligibility. This is NOT a library release.

## Harvest register
| Function | Role | Source location (candidate line) | Status | Reuse requirements |
|---|---|---:|---|---|
| RunCopiedProjectMetadataPass | recursive IAM/IPT target inventory; drawing-folder/list inventory; metadata processing | 4447 | CODE_REVIEWED, BLOCKED | Requires sTargetFolder, old/new prefixes, oActualMap, oDwgList, sDwgEntryPath, bFromDwg, logging, and explicit model skip flag. Must prove correct drawing population and save/readback. |
| SwapStaticPartsListProjectCodes | update already-static drawing Parts List cells | 5330 | INVESTIGATING | Verify PartsListCell.Static and cell iteration on target Inventor version, preservation of nonstatic cells, override readback. |
| SwapForeignProjectCodes | replace PJ##### references in string properties | 5371 | BLOCKED | Wildcard replacement can modify unrelated historical references; catch silently swallows setter failures. Restrict to approved old prefix and log failures. |
| SwapPrefixInPropertySet | iterate all string properties in one PropertySet | 5406 | CODE_REVIEWED, NOT TESTED | Replace silent Catch, establish allowed sets/fields and dry-run before mutation. |
| ReplacePrefixToken | regex token-boundary old-to-new prefix substitution | 5426 | CODE_REVIEWED, NOT TESTED | Unit-test PJ code shapes, embedded strings, suffixes, case and boundaries. |
| ReplaceExistingPrefix | named property swap | 5434 | INVESTIGATING | Silent Catch hides missing vs write failure. |
| SetPropertyValue | named property setter/add fallback | 5448 | INVESTIGATING | Catch-all may mistake write failure for missing property; isolate lookup exception. |
| ReplaceLeadingProjectCode | SPECIFICATION leading PJ#####- prefix swap | 5460 | INVESTIGATING | Only hyphen form recognized; silently swallows errors; may replace nonapproved old prefix. |
| SetExistingNonblankProperty | PROJECT NUMBER setter | 5477 | INVESTIGATING | Unconditional new project value; require provenance/approval and exception reporting. |
| PadFiveDigitProperty | numeric custom field padding | 5491 | REJECTED / KNOWN DEFECT | Matches exactly five digits then prepends 0, producing six. Correct semantics for 1-4 digits to 5; never promote this version. |

## Critical findings
1. VERIFIED SOURCE DEFECT: PadFiveDigitProperty uses regex ^[0-9]{5}$ and writes "0" & sOld; known weekend defect has regressed in BB15 candidate.
2. RunCopiedProjectMetadataPass collects models recursively from target folder and drawings from oDwgList, entry path and entry drawing folder, but the list may be empty depending on invocation; source alone does not prove correct runtime coverage.
3. Model loop updates Design Tracking and Custom sets; drawing loop updates Custom, Design Tracking and Summary. Model Summary properties are not included.
4. Several helper functions use Catch without diagnostic, potentially hiding failed property writes.
5. Wildcard foreign PJ replacement can touch unrelated references; explicit old-prefix matching preferred.
6. Drawing Parts List static-cell update requires Inventor version-specific API and saved readback validation.
7. The known-good MU example Loop_Through_All_open_Documents_Update_Titleblocks_PJ00198_Rev 0.iLogicVb provides explicit document iteration and custom property replacement, but is not proof of unattended background processing.
8. Audit all call sites and branches; earlier property-only path divergence bypassed corrected helper functions.

## Archive policy (PROPOSED)
Each reusable function must have: canonical name and purpose; exact source path/blob/commit and line range; Inventor version; inputs/outputs and side effects; API dependencies; supported document types; error/rollback behavior; test fixture; expected/actual logs; CODE_REVIEWED / LOCALLY_TESTED / WORKPLACE_VALIDATED / APPROVED evidence; known defects and regression cases; reuse license and limitations.
Keep candidates, rejected patterns and verified functions separate. Do not copy helpers into a shared production library until APPROVED.

## Next actions
- Fix padding regression and missing failure diagnostics in a separate candidate commit, not silently in the uploaded baseline.
- Add dry-run discovery and mutation preview; test both model and drawing paths and static Parts List cells.
- Compile and execute on target Inventor; verify persistence and untouched metadata; attach logs and exact version to this audit.
- On successful validation, extract only independently tested functions into versioned iLogic archive and update provenance index.
- Consider BEEXCITED-AI platform-wide research-first and function-harvest policy; currently CANDIDATE, not adopted.
