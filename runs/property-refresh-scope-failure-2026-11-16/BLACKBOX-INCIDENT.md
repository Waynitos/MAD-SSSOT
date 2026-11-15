# BLACKBOX INCIDENT — Property Refresh scope failure and iLogic Assassin gate breach
Date: 2026-11-16 | Status: VERIFIED process/requirements coverage failure; technical repair INVESTIGATING; full APPLY BLOCKED.
Repository: Waynitos/MAD-SSSOT | Branch: feature/sweeper-v2.2.34-existing-target-repair

## Failure
Weekend audit focused on padding, setter exceptions, Save2 and Close lifecycle but failed to check original drawing discovery and recursive model coverage. Monday PWTP-02 still searches top-level of one target folder for IAM/IPT/IDW/DWG; drawings actually reside in original GA drawing folder, while copied models are in target folder. The original Super Clean Sweeper contains oDwgList and sDwgEntryPath, but standalone pilot does not receive or reconstruct that list. It updates a hardcoded subset of model properties and resets drawing metadata to constants instead of performing approved project-prefix replacements. This is a requirements-coverage failure, not just an API defect.
MU identified gap via independent Grok review after weekend audit. Grok's suggested repair is unverified and must be assessed, not blindly adopted.

## Monday test evidence
Uploaded Desktop log BBn_PROPERTY_REFRESH_PWTP02_20261116_060859.log: APPLY; scanned=5, changed=0, skipped=4, failed=0. Four already-open IAM files skipped; one IAM opened/closed with changes=0. No property write or save tested. This log is not committed here; MU retains original. Friday APPLY had reported 411 scanned, 37 candidates, 31 skipped and then Inventor crash; crash root cause remains unknown.

## Process failures
1. iLogic Assassin research-first directive not demonstrated: no complete comparison with prior successful rules, original call chain, folder topology, drawing list and model traversal before implementing.
2. MAD reviewed individual functions rather than end-to-end acceptance criteria and actual data population.
3. Test harness counted skipped already-open documents toward five-file limit and yielded no mutation candidates.
4. Missing drawing/model population counts allowed silent zero changes to appear successful.
5. Hardcoded drawing revisions, DRAWN and other metadata risk destructive changes.
6. Weekend audit/commits not reconciled before Monday handover; competing candidate offered.

## Source references
- Original: scripts/ilogic/TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb
- Friday baseline: scripts/ilogic/experiments/BBn_PROPERTY_REFRESH_ONLY_PWTP_01.iLogicVb (blob 5279780a5ee5512a8e740f4884f957a57781c58b)
- Weekend pilot: scripts/ilogic/experiments/BBn_PROPERTY_REFRESH_ONLY_PWTP_02_PILOT.iLogicVb (blob 6212461c91e77116c49931228d0745e8619d200e)
- Prior audit: runs/property-refresh-crash-2026-11-14/PWTP-PROP-02-audit.md

## Required corrective gates (PROPOSED; not yet implemented)
1. iLogic Assassin: find/review proven internal and external patterns; document original call sites, drawing list construction, model reference graph, and known-good metadata rules before writing code.
2. Discovery-only DRY RUN: explicitly enumerate GA drawing folder, entry drawing, oDwgList or reconstructed list; recursive target model set; log META-DWG-FOLDER, META-DWG-COUNT, model count, exclusions and missing scope. Standalone rule cannot access another rule's local variables without passing them.
3. Approved mutation mapping: enumerate relevant string properties and exact old/new PJ prefix semantics; preserve unrelated metadata, revisions and dates; distinguish JC-derived target parts from external libraries.
4. Acceptance tests: at least one known model and one known drawing candidate; pre/post values, save and reopen persistence, independent saved/failed counts, full population coverage; small batches before full APPLY.
5. MAD AA/DA/SSA must test scope contract and negative cases, not just implementation. No production change without evidence.
6. Mandatory GitHub/automation reconciliation before handover and no competing unreviewed candidate.

## Hive Knowledge Contribution
CANDIDATE: Function-level correctness without workflow discovery coverage creates false-positive success. Reusable gate for all BEEXCITED coding agents; promote via BEEXCITED-AI only after review. Original evidence remains in MAD-SSSOT.