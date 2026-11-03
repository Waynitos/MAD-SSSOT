# SSA — Synthesiser Verdict: GA Integrity Pass Root-Cause & Fix

**Run date**: 2026-11-03  
**Project**: INVENTOR - CLEAN SWEEPER SUITE  
**Rule**: TRAVERSE_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb  
**Trigger**: GA still contains old-segment-style sub names after Drawing Copy Mode run

---

## Two independent confirmed bugs

### Bug 1 — GA never found (GA discovery failure)
The integrity pass looks for a GA only in the ACTIVE drawing's model refs. The run was started from `PJ00205-GTA-3450-6-000001.dwg` which has **0 model refs** → integrity pass skipped entirely. Log evidence: `PRE-TREE: no GA .iam found in active drawing refs — skipped`.

### Bug 2 — Rename map has no old→new entries (map coverage gap)
All 53 entries in `oRenameMap` are identity mappings (`new name → same new name`). The old segment-style GA child names (`PJ00205-E3432-8-TANK UPPER ASSEMBLY.iam`) were **never in any drawing ref** — the drawings already had new names when this (repeat) run executed. So `oBasenameRenameMap` contains zero segment-rename entries. The integrity pass would silently do nothing for old-style GA children even if the GA had been found.

---

## SSA verdict on approach

Both agents agree on one thing: the GA discovery fix is a simple, uncontested, must-do change.

**On the broader mapping gap**, the verdict is a **pragmatic hybrid**:

- **DA wins the premature-open argument**: Opening a large GA assembly with potential broken refs, DA virtuals, and Vault checkout prompts BEFORE the user has confirmed the rename form is the highest-crash-risk moment in the workflow. This project has already crashed Inventor once this session. Defer any pre-form GA open.

- **AA wins the "drawing-refs are always incomplete" argument**: The GA is a superset of all drawing refs. A rename map built solely from drawing refs will always miss GA-direct children. The long-term correct solution is to surface GA children in the rename form — but only AFTER the architecture is stable and the history/checkbox feature is working (so the form doesn't bloat on repeat runs).

### Immediate fix (implement now)

**Fix 1 — GA discovery**: Replace the active-drawing-only ref scan with a scan of `ThisApplication.Documents` for an open `.iam` in the same project folder hierarchy. If exactly one is found, use it as the GA. If multiple, show a compact picker. If none, show a file picker. This is a safe Documents collection scan — no assembly open required.

**Fix 2 — Integrity pass fallback for unresolved GA children**: When a GA child's basename is:
- NOT found in `oTargetInv` (target folder inventory), AND  
- NOT found in `oBasenameRenameMap` (no explicit rename mapping)

Then:
1. Check if the source file physically exists at the occurrence's current path (`System.IO.File.Exists(sOccPath)`)
2. If YES → `File.Copy(sOccPath, sOccExpected, True)` using the SAME basename into target folder → `oOcc.Replace(sOccExpected, True)` → log `INTEGRITY-COPY-AS-IS`
3. If NO → log `INTEGRITY-WARN-MISSING` (file gone from source too — nothing we can do)

This means old-style GA children land in the target folder under their original names (not renamed), which correctly wires the GA tree to target folder files. They won't have the new segment-style names unless the user maps them in the form — but that is the **next iteration** (GA-Tree-First form extension, deferred to after history feature).

### Deferred (next update after history/checkbox stable)
Extend Phase 0 to enumerate GA direct children and add them as additional rows in Step 2 form — but ONLY after the GA is already open in Inventor session (i.e. user has it open, detected via `ThisApplication.Documents`), never by cold-opening it. This gives the user explicit control over old→new mapping for GA-direct children without the pre-form crash risk.

---

## iLogic API audit notes

- `ComponentOccurrence.Replace(newPath, True)` — `True` = replace all identical occurrences. Well-supported. Known failure modes: DA-virtual assemblies (throws), suppressed occurrences (silently succeeds or silently fails — verify via `oOcc.ReferencedFileDescriptor.FullFileName` after call). Add post-Replace verification.
- `AssemblyDocument.ComponentDefinition.Occurrences` — safe read-only enumeration at depth 1. No open/resolve triggered. Stable.
- `DrawingDocument.ReferencedDocuments` — used to get model refs. Reliable for `.iam`/`.ipt` refs that are actually loaded. Returns nothing for refs that Inventor cannot resolve (broken links, not-yet-opened files). This is WHY old GA children never appear — they are NOT referenced by drawings, only by the GA assembly.
- `ThisApplication.Documents` — safe scan of currently open documents. No IO, no resolve, no crash risk.

---

## Implementation checklist
- [ ] Fix 1: Replace `oScanRefs`-based GA discovery with `ThisApplication.Documents` scan
- [ ] Fix 2: Add copy-as-is fallback in integrity pass `WalkAndReplace` for unresolved GA children
- [ ] Add post-Replace verification: read back `oOcc.ReferencedFileDescriptor.FullFileName` and compare to expected; log `INTEGRITY-VERIFY-FAIL` if mismatch
- [ ] Log `INTEGRITY-COPY-AS-IS` for each fallback copy performed
- [ ] Deferred: GA-Tree-First form extension (after history feature)
