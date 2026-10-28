# Clean Sweeper — Mode 6 (Copy Design) Flow Spec
_Last updated: 2026-10-28_

This document is the authoritative spec for Mode 6. Any session working on
TRAVERSE_fixed.iLogicVb must read this before making changes.

---

## Entry point

The rule is attached to the GA drawing (.idw). The user opens the GA drawing
and runs the rule from it. The rule detects `kDrawingDocumentObject`, iterates
`ReferencedDocuments` to find the first `kAssemblyDocumentObject`, and uses
that as `oAsmDoc`. `sTargetFolder` is derived from `oAsmDoc.FullFileName`, NOT
from `ThisDoc.Path` (which would point to the drawing folder).

---

## Step-by-step flow

```
User opens GA drawing → runs rule from GA drawing
         │
         ▼
① FolderBrowserDialog — "Select folder for new GA model"
  Seeds: last chosen dest → drawings folder → source assembly folder
  Result → sTargetFolder for the ENTIRE run (all SaveAs copies land here)
         │
         ▼
② ShowCopyDesignConfigForm
  - New project prefix (applied to std AND non-std)
  - Up to 5 segment find/replace pairs
  - ☑ Localize non-std parts into Non Std Parts subfolder  [default: ON]
  - ☑ Keep existing drawing model names (skip rename step) [default: OFF]
  - Folder structure: CLEAN SINGLE FOLDER / HONOUR EXISTING
  - DRAWING UPDATE section:
      ☐ Update drawings after TRAVERSE
      Drawings folder browse (flat .idw folder)
  NOTE: destination folder is NOT in this form — it was captured in Step 1
         │
         ▼
③ Phase 0 scan + Drawing Model Rename form
  Only runs when bUpdateDrawings=True AND sDrawingsFolder is set.
  RunPhase0DrawingScan: opens each .idw silently, reads ReferencedDocuments,
  builds list of {drawing basename, List(Of model basenames)}.

  If bKeepDrawingModelNames=True:
    Self-map: all scanned model basenames → same name (tier-1 lock)
    No form shown
  Else:
    ShowDrawingModelRenameForm:
      Left column  = old model basename (read-only)
      Right column = new model basename (editable on FIRST appearance only;
                     subsequent appearances of same old model are GREYED/LOCKED
                     showing the same new name — one old name → one new name, enforced)
      ☑ Match model states? per drawing row
    → oExplicitModelRenameMap (old basename → new basename)
    → oDrawingStateMatch (drawing basename → True/False)

  Tier-1 exclusion: every key in oExplicitModelRenameMap is IMMUNE to all
  string rules (prefix swap, segment replace, non-std). Enforced via
  Continue For in BuildCopyDesignRenameMap.
         │
         ▼
④ ShowBatchSelectionForm
  Scans assembly tree for old P-prefixes.
  User selects which prefix tokens to target.
  String rules configured here (prefix swap already pre-filled from Step 2).
         │
         ▼
⑤ BuildCopyDesignRenameMap
  Builds oRenameMap: old full path → new full path for every file in tree.
  Rename priority:
    1st — oExplicitModelRenameMap (tier-1, user-confirmed drawing model names)
    2nd — string rules (prefix swap + segment rules, skipping tier-1 keys)
  Non-std files → Non Std Parts subfolder if bLocalizeNonStd=True
         │
         ▼
⑥ TRAVERSE (ProcessLevel recursive walk)
  GA assembly SaveAs → new name → sTargetFolder  ← FIRST FILE WRITTEN
  All subs: SaveAs using oRenameMap entry, land in sTargetFolder
         │
         ▼
⑦ Post-traversal passes (existing sequence, unchanged)
  RunDerivedAndParamFixPass
  RunFixInternalRefsPass
  RunPjPropertySyncPass
  RunBrowserNodeResetPass
  Document cleanup pass (closes non-dirty session docs)
         │
         ▼
⑧ RunDrawingUpdatePass  ← BEFORE cleanup closes session docs
  Called only when bUpdateDrawings=True AND oSelectedDrawings is non-empty.
  Loops selected .idw paths (from ShowDrawingSelectionForm checkpoint).
  For each drawing:
    ReplaceReference: old doc → new doc for every oExplicitModelRenameMap entry
    If oDrawingStateMatch[drawing]=True → re-assert model states per view
    100% resolved → save drawing (DRAW-OK)
    Any unresolved → skip save (DRAW-PARTIAL-SKIP, logged for manual repair)
         │
         ▼
⑨ ShowDrawingSelectionForm checkpoint
  Shown BEFORE RunDrawingUpdatePass fires.
  Lists all .idw files in sDrawingsFolder.
  Three tiers:
    PRE-TICKED   — in Phase 0 scan AND has refs matching oRenameMap
    UN-TICKED    — in Phase 0 scan but no matching refs this run
                   (suffix: "  (no matching refs in this run)")
    UN-TICKED    — NOT in Phase 0 scan (orphan/obsolete copy)
                   (suffix: "  (not in original drawing scan)")
  Allows partial re-runs: user can untick drawings to skip.
         │
         ▼
⑩ Pass manifest written (WritePassManifest)
  Auto-numbered: _RenameMap_Pass1.txt, _Pass2.txt, etc.
  Tab-separated OLD PATH → NEW PATH table, sorted, written to sTargetFolder.
  Entries where only folder changes (same filename) tagged [RELOCATE-ONLY].
         │
         ▼
⑪ Top assembly save (oAsmDoc.Save() — NOT ThisDoc.Save)
  Vault checkout note if needed.
  Rule complete popup.
```

---

## Key variable notes

| Variable | What it is | Set where |
|---|---|---|
| `sTopAssemblyFullName` | Full path of SOURCE assembly (original, pre-copy) | Line ~281, from `oAsmDoc.FullFileName` |
| `sTargetFolder` | Destination folder for ALL new copies | Step 1 FolderBrowserDialog |
| `oExplicitModelRenameMap` | Tier-1 map: old model basename → new basename | Phase 0 form or self-map |
| `oDrawingStateMatch` | Per-drawing flag: re-assert model states? | Phase 0 form |
| `oPhase0Data` | Raw Phase 0 scan results | Declared at Sub Main top level (scope!) |
| `oRenameMap` | Full rename map: old full path → new full path | BuildCopyDesignRenameMap |

---

## Critical iLogic sandbox constraints

- `System.Drawing.Primitives` is ENTIRELY blocked — no `Color`, no `SystemColors`.
  Never use `ForeColor` / `BackColor` on any control. Use text labels for visual
  differentiation instead (e.g. greyed appearance via text suffix, not colour).
- `System.Drawing.Font` constructor is blocked.
- `Button.ToolTipText` is not a member in this sandbox.
- VB.NET scope: variables declared inside an `If` block are not visible outside it.
  `oPhase0Data` MUST be declared at Sub Main top level (before any `If` block).
- VB.NET `If`/`Else` same scope: cannot declare same variable name in both branches.
  Declare once before the `If`.

---

## Commit history (key milestones)

| Commit | What |
|---|---|
| `ef3c960` | Tier-1 guard in BuildCopyDesignRenameMap |
| `6329f41` | oPhase0Data hoist attempt (insufficient) |
| `9d47366` | oPhase0Data hoisted to Sub Main top; all Color/SystemColors removed |
| `ced52df` | Entry point fixed: DrawingDocument → walk to referenced AssemblyDocument |
| `8cced2b` | sTargetFolder from asm path not ThisDoc.Path; oAsmDoc.Save not ThisDoc.Save |
| `3b79849` | Dest folder browse added to config form (superseded by 33be0a1) |
| `e0511c3` | Dest folder browser seeded from drawings folder |
| `33be0a1` | Dest folder promoted to Step 1 FolderBrowserDialog before config form |
