# BLACKBOX-15 — comparative code review and corrective candidate
Date: 2026-11-16 | Status: CODE_REVIEWED (partial source comparison), NOT COMPILED, NOT LOCALLY_TESTED, NOT WORKPLACE_VALIDATED.
Inputs: MU-uploaded 5444-line TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN_ENHANCEMENT_PROPERTY_TEST_FIXED (29).iLogicVb and proven Loop_Through_All_open_Documents_Update_Titleblocks_PJ00198_Rev 0.iLogicVb.

## Root cause confirmed in supplied source
Property-only mode has divergent code paths. The early NOTHING-TO-COPY path calls RunCopiedProjectMetadataPass, which enumerates recursive target IAM/IPT and drawings from oDwgList, sDwgEntryPath and entry drawing folder. The later property-only completion path instead calls ApplyReferencedDocsRebadge and ApplyOpenDrawingsRebadge. The latter calls RebadgeOneDrawing, which resets drawing title block metadata and may turn BOM cells static. Thus existing fixes are bypassed depending on flow. The known-good sample demonstrates explicit Document iteration and custom iProperty string replacement; it does not establish background folder discovery or static Parts List behavior.

## Candidate prepared (local only, not committed to repository)
CLEAN_SWEEPER_PROPERTY_TEST_BB15_REVIEW_ONLY.iLogicVb. Minimal patch to user-uploaded source: route later property-only branch to RunCopiedProjectMetadataPass; add META-MODEL-COUNT; update only already-static Parts List cells; remove drawing-number overwrite in metadata pass; log dirty-retained and close failures. The user-visible sandbox candidate must be compiled in Inventor before testing.

## Risks and unresolved defects
The candidate still inherits wildcard replacement of any foreign PJ##### and legacy silent catches in property-set helper functions; it may modify historical references unintentionally. It retains existing metadata function's unconditional PROJECT NUMBER setting and padding logic. Other full-sweep and relink code paths remain unchanged, including older reset functions. No source-level proof of safe Vault checkout, PartsListCell.Static API compatibility with Inventor 2017, or reliable save/readback. Need DRY RUN preview and controlled small batch before any APPLY. No runtime validation claimed.

## Mandatory next actions
1. iLogic Assassin compare source against known-good sample and original full-sweep call graph; enumerate all property-only paths and destructive operations.
2. Add discovery-only and mutation-preview dry-run with exact model/drawing counts and static-cell preview.
3. Compile in target Inventor, check PartsListCell.Static, test one known IAM/IPT and one IDW with a static override on disposable checked-out copies.
4. Verify save/readback and unchanged unrelated metadata. Record log, exceptions and commit only after MU approval.
5. Cross-project Hive lesson: always audit call sites, branch conditions and test population, not only helper functions. Status CANDIDATE for BEEXCITED-AI adoption.