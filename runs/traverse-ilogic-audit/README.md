# MAD Run: TRAVERSE iLogic Audit

**Date:** 2026-10-24
**Topic:** TRAVERSE_fixed.iLogicVb — Autodesk Inventor iLogic assembly tree traversal and file rename rule
**File audited:** TRAVERSE_fixed.iLogicVb (8,052 lines, iLogic VB.NET)
**Cycle:** AA → DA → SSA + fix proposals
**Session:** https://claude.ai/code/session_01TAkMGJHWx8Am8HumHMEoSx

---

## Background

8,052-line iLogic VB.NET rule for Autodesk Inventor that recursively traverses an assembly tree and renames/replaces parts and sub-assemblies by swapping a file name prefix or segment. Handles Vault-managed files, derived source parts, parameter table xlsx links, Content Centre exclusions, virtual components, and more.

**Modes:**
- Mode 1: Prefix swap (file must START WITH find text)
- Mode 2: Segment replace (CONTAINS anywhere), using Vault Copy Design-style 5-phase engine
- Mode 3: Consolidate only (copy to target folder, no rename)
- Mode 4: Batch P-prefix scan and swap
- Mode 5: Verify only (read-only scan for old-prefix references)
- Mode 6: Copy Design (combines all — the recommended gold path)

**User's observed behaviour:** "No major issues if all modes ran as a batch in mode 6. If I repeated it on other modes sometimes due to the cached versions of historic subs it missed the renaming of define pass runs."

---

## SSA Verdict (Summary)

**Architecture:** Sound. 6-mode split, Mode 2 multi-phase engine, bottom-up traversal, and Mode 6 gold path are all correct.

**10 of 12 DA weaknesses confirmed** (2 rejected). 8 copy-paste VB.NET fixes provided.

**Root cause of reported symptom (Fix A):** `oProcessedResults` cache stores False ("no changes") results. When the same document is reached from a second branch in the same traversal, the cached False short-circuits re-exploration — even though sibling renames since Branch A visited it may have made the document's internal refs stale. Fix: only cache True (changed) results.

**Single most impactful structural change:** Make Mode 6 the default interactive entry point. Demote Modes 1–5 to an "Advanced" submenu. Eliminates the reported symptom by directing users to the gold path without changing how any mode works.

---

## Fixes (Priority Order)

| Fix | DA # | Risk | Effort | Description |
|-----|------|------|--------|-------------|
| A | #1 | High | Small | Cache invalidation: only cache True, not False results (`ProcessLevel`) |
| B | #2 | High | Small | Phase 3 sort: separator count not path length (~line 939) |
| C | #4 | High | Small | Phase 2 failure guard: verified-copy set filters Phase 3 + Phase 4 |
| D | #10 | Med | Small | Excel DisplayAlerts: always restore True; null-guard GetSetExcelApp |
| E | #8 | Med | Small | Log path: LocalAppData fallback for UNC-redirected corporate Desktop |
| F | #3, #5 | Low | Small | SilentOperation Try/Finally; stale pre-built map clear on cancel |
| G | #7 | Low | Small | Snapshot: timestamp header + path existence warning on read |
| H | #11 | Low | Small | Mode 3: post-run skipped-file summary MessageBox |

**Partially confirmed (documented, no code fix):** DA #6 (suppressed LOD components), DA #9 (no mid-run cancel — iLogic API limitation)

**Rejected:** DA #12 (sFind=sReplace placeholder — Phase 4 does not use sFind)

---

## Win-Win Enhancements

| # | Enhancement | Benefit |
|---|-------------|---------|
| WW1 | Mode 2 pre-map dry-run preview before Phase 2 | Gives Mode 2/6 the same pre-flight confirm Mode 3 already has; zero extra disk ops |
| WW2 | Mode 5 verify: list specific residuals not just count | Actionable output — user knows exactly which files need another pass |
| WW3 | Final rename map appended to log | Post-run audit trail; usable as manual revert input |
| WW4 | Mode 6 file-count confirmation after map build | Two confirmation points (count + full list) before any Phase 2 disk writes |

---

## Files

| File | Contents |
|------|----------|
| `AA-output.md` | Advocate: 8 architecture strengths, 5 honestly acknowledged weaknesses |
| `DA-output.md` | Devil's Advocate: 12 structural weaknesses with code evidence |
| `SSA-output.md` | Synthesizer: verdict table, 8 copy-paste VB.NET fixes, 4 win-win enhancements |

## Script

`scripts/ilogic/TRAVERSE_fixed.iLogicVb` — the audited script (unmodified; fixes are in SSA-output.md as copy-paste blocks).
