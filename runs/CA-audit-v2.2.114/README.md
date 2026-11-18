# Run: CA-audit-v2.2.114

**Type:** CODE_ASSASSIN independent source audit  
**Date:** 2026-11-19  
**Rule version:** v2.2.114-P3-STAB  
**Trigger:** Independent review requested after ChatGPT C1–C8 assessment; uploaded source file reviewed

## Files

| File | Contents |
|---|---|
| `CA-report.md` | Full 10-finding audit (CA-1 through CA-10) with ChatGPT comparison table |

## Summary

10 findings total. All 8 ChatGPT findings (C1–C8) confirmed with amplifications. 3 new findings not in ChatGPT review (CA-6, CA-9, CA-10).

**Critical:**
- **CA-1** (PASS1-FILTER nukes rename map) — direct cause of "old subs aren't being swapped out"
- **CA-2** (`CloseAll(True)` closes user documents)

**High:**
- CA-3 (`SkipAllUnresolvedFiles` hides incomplete repair)
- CA-4 / CA-5 (no Phase 3 failure gate before Drawing Relink)
- CA-9 (Vault read-only parent blocks Phase 4)
- CA-10 (SaveAs fallback → XML corruption)

**Next step:** Fix CA-1 (remove `oRenameMap.Clear()` from PASS1-FILTER or resolve Drawing List keys to disk paths before seeding `oPass1Keys`).
