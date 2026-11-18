# MAD Run: sCanonMiddle-fix-v2.2.113

**Date:** 2026-11-19  
**Rule:** TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN_ENHANCEMENT.iLogicVb  
**Version under review:** v2.2.113-FIRST-TOK  
**Topic:** `sCanonMiddle` extraction guard in `DetectStringAnomalies`

## Background

In the 18/11/2026 run, a double-prefix GA (`PJ00204-PJ00190-3430-V0.iam`) caused `DetectStringAnomalies` to extract `sCanonMiddle = "-PJ00190-3430-"`. This generated the wrong STRING-SUGGEST `-3430- -> -PJ00190-3430-`, which would have re-inserted the obsolete project code into 43 already-correct filenames if the user had accepted it.

v2.2.112/113 introduced a regex guard that strips the embedded PJ token and recovers the correct `-3430-`. v2.2.113 added FIRST-TOK comparison (only first token of each file's middle compared against canon).

## Files

| File | Contents |
|---|---|
| `AA-output.md` | Strongest case FOR the fix |
| `DA-output.md` | Strongest case AGAINST the fix |
| `SSA-output.md` | Synthesiser verdict |

## SSA Verdict (summary)

Ship v2.2.113 with the regex guard as-is. **Mandatory before next run:** add a warning log when the `sCanonMiddle = ""` fallback fires (silent suppression is worse than the original wrong suggestion). **Roadmap TODO:** migrate `sCanonMiddle` derivation to `sDwgEntryPath` as structurally correct long-term fix.
