# MAD Run — iProperty Reference Map for Clean Sweeper

**Topic:** Use Autodesk Inventor iProperties as a temporary/permanent metadata tagging system to replicate Vault Copy Design's internal reference map during the Clean Sweeper Suite's copy/rename/relink workflow.

**Date:** 2026-11-04  
**Project:** INVENTOR - CLEAN SWEEPER SUITE (PJ00205 test run context)  
**Triggered by:** Waynito — session observation that drawing refs were missing model links after GA traverse

## Files

| File | Contents |
|---|---|
| `AA-output.md` | Strongest case FOR iProperty tagging |
| `DA-output.md` | Strongest case AGAINST iProperty tagging |
| `SSA-output.md` | Synthesis verdict |

## SSA One-Line Verdict

> **Adopt NEW file tagging only (zero extra cost, real gains). Reject OLD file tagging (Vault conflicts, O(n) cost). Automate the stripout. Implement after RunLog + GA-first architecture are stable.**

## Context

The Clean Sweeper currently maintains its old→new reference map via:
- In-memory dictionaries (die on session end/crash)
- Text RunLog file (`_CleanSweeper_RunLog.txt`)

The proposal was to additionally embed the map as iProperties on the files themselves, mirroring how Vault's SQL database tracks copy relationships via GUIDs.

The MAD cycle identified that the proposal is correct for new `_CLEAN` files (already open/saved during copy — zero extra cost) but incorrect for old source files (not checked out, O(n) open/save cost, Vault state conflicts).
