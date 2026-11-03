# MAD Run: GA Integrity Pass Root-Cause & Fix

**Date**: 2026-11-03  
**Trigger**: RMAD  
**Topic**: GA integrity pass not wiring old-segment-style GA children to new copies in target folder

## Root causes confirmed
1. GA discovery depends on active drawing having model refs — fails silently when active drawing has 0 refs
2. `oRenameMap` built from drawing refs only — old GA child names (never in drawing refs) never enter the map — integrity pass silently skips them

## Files
| File | Content |
|---|---|
| `AA-output.md` | Strongest case FOR GA-Tree-First (open GA before form, add GA children as rename rows) |
| `DA-output.md` | Strongest case AGAINST premature GA open; FOR target-folder match at integrity time |
| `SSA-output.md` | Synthesiser verdict — pragmatic hybrid: Documents-scan GA discovery + copy-as-is fallback |

## Decision
**Implement now**: Fix GA discovery via `ThisApplication.Documents` scan + add copy-as-is fallback in integrity pass for unresolved GA children.  
**Defer**: GA-Tree-First form extension until history/checkbox feature is stable.
