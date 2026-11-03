# SSA Verdict — Clean Sweeper Execution Order

**Date:** 2026-11-04  
**Session:** https://claude.ai/code/session_019z9imiuqpyH5DETSzix2Vi  
**Topic:** Correct execution order for TRAVERSE_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN

---

## Verdict

**AA wins the principle. DA wins the implementation detail. The mandated sequence is four strictly separated phases.**

The GA is the authority — AA is correct. Drawings are consumers. No drawing reference update may precede the completion of the assembly relink pass. The current implementation's inversion of this order is the root cause of the persistent "old names still in tree" symptom.

However, DA correctly identifies that "open GA and relink" is not a single atomic operation in Inventor's document model. Lazy loading, depth-N relinking, and copy atomicity each present real failure modes if the sequence is collapsed. The correct implementation is therefore DA's four-phase model, with AA's GA-authority principle embedded as the validation contract governing Phase 4.

---

## Mandated Execution Sequence

### Phase 1 — SCAN (read-only, no files touched)
1. Open active GA drawing → resolve principal GA `.iam` path
2. Walk GA tree depth-first → build full OLD→NEW basename rename map (PRE_Tree)
3. Scan all drawings in the drawings folder → collect all drawing-to-model refs
4. Merge: every drawing ref must exist in the GA map
5. Any drawing ref NOT in the GA map → logged as `ORPHAN-WARN` (not an abort, but flagged for user review before proceeding)
6. Present Step 2 rename form to user — map is the data source, not drawing scan

### Phase 2 — COPY (atomic, no Inventor documents opened)
1. Copy every file in the rename map from source to target folder with new name
2. Verify every copy succeeded (`File.Exists` on destination)
3. If ANY copy fails → log `COPY-FAIL`, abort entire run, report to user
4. No `.iam` or `.ipt` or `.dwg` is opened during this phase
5. Originals are untouched — rollback is simply "delete the target folder"

### Phase 3 — RELINK ASSEMBLY TREE (depth-last: leaves first, GA last)
1. Take the full occurrence list from PRE_Tree, sorted by depth descending (deepest parts first)
2. For each file: open the copied new file in the target folder
3. Iterate `ReferencedDocumentDescriptors`, look up each old ref path in the rename map
4. Call `ReplaceReference` for every match found
5. Save and close before moving to the next file
6. Log `RELINK-OK` / `RELINK-SKIP` / `RELINK-FAIL` per file
7. By the time the GA itself is processed (last), all its children are already closed-and-saved with corrected descriptors — Inventor resolves them cleanly

### Phase 4 — RELINK DRAWINGS (validation + correction, drawings last)
1. For each drawing in the scan list: open it
2. For each model reference: look up in the rename map
3. If found in map → `ReplaceReference` to new path → `DRAW-RELINK-OK`
4. If NOT found in map → `DRAW-ORPHAN-ERROR`: log the drawing filename and the unresolved ref path; do not update that reference; continue to next drawing
5. Save and close each drawing
6. At completion: surface a summary of all ORPHAN errors to the user — these require manual resolution

---

## Validation Contract (AA principle embedded)

> **The rename map built in Phase 1 from the GA tree walk is the single source of truth.**  
> A drawing reference is valid if and only if it appears in this map.  
> A reference outside the map is an orphan — it belongs to a different project, revision, or branch, and must never be silently copied or silently skipped.

This contract makes the ORPHAN condition visible rather than burying it. The user can then decide: add the orphaned model to the GA tree (correct the assembly), exclude the drawing from this run, or accept the orphan and handle it manually.

---

## What the Current Implementation Gets Wrong

| Step | Current behaviour | Required behaviour |
|------|------------------|-------------------|
| Discovery | Drawing scan drives model discovery | GA tree walk drives map; drawing scan is validation only |
| Copy | Files copied during/after form | Phase 2: all files copied before any Inventor doc opened |
| Relink | Drawings updated, GA internal refs NOT updated | Phase 3: GA tree relinked first (leaves→GA); drawings last |
| Error handling | Orphaned drawing refs silently processed | ORPHAN-ERROR surfaced; user must resolve |

---

## Impact on Rule Architecture

The current `RunDrawingCopyMode` function conflates all four phases. The refactor must separate them into distinct sub-routines:

- `ScanPhase()` → returns rename map + orphan list
- `CopyPhase(renameMap)` → returns copy result (all-OK or abort)
- `RelinkAssemblyPhase(renameMap)` → walks depth-last, relinks each .iam/.ipt
- `RelinkDrawingPhase(renameMap)` → validates + updates each .dwg, surfaces orphans

This separation also makes each phase independently testable and re-runnable if interrupted.
