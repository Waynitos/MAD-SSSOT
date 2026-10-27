# MAD Run: Drawing Re-Association Outside Vault

**Date:** 2026-10-27  
**Project:** INVENTOR - CLEAN SWEEPER SUITE  
**Trigger:** RMAD  

## Question

Can Vault Copy Design's drawing/reference re-association behaviour (updating drawing `.idw`/`.dwg` references to point to newly renamed/relocated subassemblies and parts) be replicated using iLogic TRAVERSE rules and COM automation outside Vault?

## Context

- Existing TRAVERSE rule (Clean Sweeper Wizard) walks a GA assembly tree and renames/relocates subs according to naming convention
- After TRAVERSE, drawings referencing old paths are broken
- Approaches tried: GUID matching, geometry matching, mapping tables — all found difficult
- Goal: automated post-TRAVERSE drawing repair pass

## Files

| File | Agent | Scope |
|------|-------|-------|
| `AA-output.md` | Advocate | Strongest case FOR viability |
| `DA-output.md` | Devil's Advocate | Strongest case AGAINST viability |
| `SSA-output.md` | Synthesiser | Final verdict + implementation architecture |

## SSA One-Line Verdict

**Build it, but scope it tight:** viable as a post-TRAVERSE phase using `oRenameMap` + `ReplaceReference` + `SilentOperation = True`, only saving drawings where 100% of references resolved, logging all partial failures loudly, scoped strictly to drawings referencing models inside the TRAVERSE root.

## Key Findings

1. **Root cause of current failures:** Mapping table built after files move (old paths gone from disk). Fix: capture `oDoc.FullDocumentName` before each `SaveAs` — `oRenameMap` already does this, it just needs to be kept alive into the drawing pass.
2. **Missing flag:** `oApp.SilentOperation = True` before drawing pass — without it, unresolved-reference dialogs block the COM thread.
3. **Critical timing constraint:** Drawing repair pass must run *before* the TRAVERSE session document cleanup, so old document objects are still live in session for `ReplaceReference`.
4. **Safety rule:** Never save a drawing unless 100% of its references resolved — partial-success silent failures are worse than visible broken references.
5. **Scope guard:** Only process drawings referencing models inside the TRAVERSE root — cross-project shared references cannot be safely automated.

## Recommended First Step

Feasibility spike: after a TRAVERSE run, before session cleanup, manually call `ReplaceReference` on one known broken drawing view. Validates the core COM mechanism in the specific Inventor version before full implementation (~30 min).
