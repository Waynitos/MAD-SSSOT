# SSA — Synthesiser Verdict: Drawing Re-Association Outside Vault

> **MAD Run:** drawing-reassociation-outside-vault  
> **Date:** 2026-10-27  
> **Context:** Inventor + Vault + iLogic Clean Sweeper TRAVERSE rule  
> **Question:** Can Vault Copy Design's drawing/reference re-association be replicated outside Vault using iLogic TRAVERSE rules and COM automation?

---

## Verdict

**Conditionally YES — but only for a strictly bounded problem scope, and only with a fundamentally different architecture than the team has been attempting.**

Both agents are right, but they are arguing past each other. The DA is correct about the general case (arbitrary assembly trees with shared components, in-place features, multi-project references). The AA is correct about the specific case (files renamed/relocated by the TRAVERSE in a single-project, single-root-assembly scope). The team's problem almost entirely lives in the specific case.

The key insight that resolves the tension: **the team is not trying to replicate Vault Copy Design in general — they are trying to heal drawings broken specifically by their own TRAVERSE pass.** That is a much narrower problem, and it is solvable.

---

## What the DA Gets Right (Do Not Ignore These)

### 1. Vault Copy Design is a database transaction
The DA is entirely correct that Vault's reference re-association is transactional and database-layer. Any COM-based attempt outside Vault is file-layer and therefore cannot guarantee completeness or atomicity. This is a real architectural constraint, not a solvable implementation detail.

### 2. Shared references across project boundaries are genuinely unsolvable
If a component renamed by TRAVERSE is also referenced by assemblies *outside* the TRAVERSE root, those external references will break and cannot be healed without knowing the full reference graph across all projects. The TRAVERSE rule already has `IsDocSafeToMutate` to guard against mutating originals — the same principle applies here. The drawing repair pass must be explicitly scoped.

### 3. The partial-success failure mode is real and dangerous
A drawing that appears resolved but has 10% of views still pointing at old models is worse than a drawing that is visibly broken. This is the single most important design constraint on any implementation: it must either succeed completely or fail loudly — never silently partially.

### 4. `DrawingView.ReferencedFile` is not writable in the public COM API
The DA is correct on this point. View-level path override is not exposed as a writable property in the standard Inventor COM API. The AA's reference to `ReferencedDocumentDescriptor` is the closest approach but has version-specific reliability issues.

---

## What the AA Gets Right (The Viable Path Forward)

### 1. The mapping table architecture is correct; the timing is wrong
The AA's diagnosis of *when* the mapping table must be built is the most important finding in this entire MAD cycle. The current attempts are building the map after files have moved. `oRenameMap` is already built during the TRAVERSE walk — it just needs to be kept alive and passed to a post-TRAVERSE drawing repair pass. This is a scope/lifecycle change, not a new feature.

### 2. `ReplaceReference` on `DrawingDocument.ReferencedDocuments` does work — under specific conditions
The AA correctly identifies the conditions: both the old document object and the new document must be open in the current Inventor session at the moment `ReplaceReference` is called. During a TRAVERSE run, all the model documents that were renamed are already open in the session. This is the window of opportunity: the drawing repair pass must run **before the TRAVERSE closes its session documents.**

### 3. `SilentOperation = True` is the missing flag
The team has been hitting COM thread blocks from unresolved-reference dialogs on drawing open. `oApp.SilentOperation = True` before the drawing pass is the single most likely reason the existing attempts silently fail or hang.

### 4. `.ipj` workspace redirect eliminates the largest class of broken references
For drawings where the filename did not change (consolidation / localisation mode — same name, new folder), adding the new folder root to `DesignProject.WorkspacePaths` before opening drawings lets Inventor's own resolver find them automatically, without any `ReplaceReference` calls at all.

---

## The Synthesised Architecture

This is the viable implementation path, structured to stay within the proven boundaries:

### Phase 0 — Scope definition (before TRAVERSE runs)
- Collect all `.idw` / `.dwg` drawing files that reference any model in the TRAVERSE root.
- This can be done via `DrawingDocument.ReferencedDocuments` on each drawing before the TRAVERSE — this is a read-only operation and works reliably.
- Store as `oDrawingsToPatch As List(Of String)`.

### Phase 1 — TRAVERSE runs as-is
- `oRenameMap` is built during the walk (it already is).
- At the end of the TRAVERSE, **before any session close/cleanup**, hand `oRenameMap` to Phase 2.
- Do NOT close session documents yet.

### Phase 2 — Drawing repair pass (while session documents are still open)

```vbnet
oApp.SilentOperation = True

' Add new folder root to workspace so same-name/moved files auto-resolve
Dim oProj As DesignProject = oApp.DesignProjectManager.ActiveDesignProject
oProj.WorkspacePaths.Add(sNewFolderRoot)
oProj.Save()

For Each sDrawingPath In oDrawingsToPatch
    Dim oDrawDoc As DrawingDocument = Nothing
    Try
        oDrawDoc = oApp.Documents.Open(sDrawingPath, False)  ' False = don't show
        
        For Each kvp In oRenameMap   ' kvp.Key = old full path, kvp.Value = new full path
            Dim oOldDoc As Document = Nothing
            Dim oNewDoc As Document = Nothing
            Try
                ' Old doc must already be open in session from TRAVERSE
                oOldDoc = oApp.Documents.ItemByName(kvp.Key)
                oNewDoc = oApp.Documents.ItemByName(kvp.Value)
                If oOldDoc IsNot Nothing AndAlso oNewDoc IsNot Nothing Then
                    oDrawDoc.ReferencedDocuments.ReplaceReference(oOldDoc, oNewDoc)
                End If
            Catch ex As Exception
                LogLine("DRAW-REF-FAIL: " & kvp.Key & " -> " & kvp.Value & " : " & ex.Message)
            End Try
        Next
        
        ' Verify: check for any remaining unresolved references
        Dim bClean As Boolean = True
        For Each oRef As Document In oDrawDoc.ReferencedDocuments
            If Not File.Exists(oRef.FullDocumentName) Then
                LogLine("DRAW-UNRESOLVED-REMAIN: " & sDrawingPath & " -> " & oRef.FullDocumentName)
                bClean = False
            End If
        Next
        
        If bClean Then
            oDrawDoc.Save()
            LogLine("DRAW-OK: " & sDrawingPath)
        Else
            ' DO NOT SAVE a partially resolved drawing
            LogLine("DRAW-PARTIAL-SKIP: " & sDrawingPath & " - NOT saved, manual repair required")
        End If
        
    Catch ex As Exception
        LogLine("DRAW-OPEN-FAIL: " & sDrawingPath & " : " & ex.Message)
    Finally
        If oDrawDoc IsNot Nothing Then oDrawDoc.Close(False)
    End Try
Next

oApp.SilentOperation = False
```

### Phase 3 — Verification
- Run a read-only scan (analogous to Mode 5 on models) that opens each drawing and reports any remaining unresolved references.
- Output to the decisions log as `[DRAW-UNRESOLVED]` entries.
- A drawing with any `[DRAW-UNRESOLVED]` entries is **never silently accepted as fixed** — it is flagged for manual repair.

---

## Critical Scope Guards (Non-Negotiable)

These constraints prevent the DA's failure modes from occurring:

| Guard | Reason |
|-------|--------|
| Only process drawings that reference models **inside the TRAVERSE root** | Prevents cross-project reference corruption |
| Only save drawings where **all** references resolved | Prevents the partial-success silent failure mode |
| Log `DRAW-PARTIAL-SKIP` for any drawing not saved | Makes partial failures loud, not silent |
| Run Phase 2 **before** session document cleanup | Ensures old doc objects are still live in session for `ReplaceReference` |
| Never attempt to repair drawings for **shared/standard library components** | These are outside the TRAVERSE scope by definition |

---

## What This Does NOT Solve (Honest Boundaries)

- **Drawings that were already broken before the TRAVERSE ran** — not in scope.
- **Drawings referencing models outside the TRAVERSE root** — out of scope, cannot be safely automated.
- **In-place / adaptive features** — COM cannot reconstruct positional constraints; these require manual repair.
- **Drawings in other projects that shared the renamed components** — the DA is correct that these will break; the answer is to scope the TRAVERSE to avoid renaming shared components (which `IsDocSafeToMutate` already does for model files).
- **Configuration-specific drawing views** — `ReplaceReference` operates at the document level; view-specific configuration mismatch after rename requires manual inspection.

---

## Connection to Existing TRAVERSE Architecture

The repair pass architecture maps directly onto the existing rule structure:

| Existing | Maps to |
|----------|---------|
| `oRenameMap` dictionary | Phase 1 → Phase 2 data handoff |
| `RunDerivedAndParamFixPass` | Analogous post-traversal sweep; drawing pass is a new `RunDrawingRepairPass` |
| Mode 5 (VERIFY ONLY, read-only scan) | Phase 3 drawing verification (`[DRAW-UNRESOLVED]` reporting) |
| `IsDocSafeToMutate` | Scope guard for drawing pass (only process drawings that reference TRAVERSE-root models) |
| Decisions log format | Extend with `DRAW-OK`, `DRAW-PARTIAL-SKIP`, `DRAW-UNRESOLVED-REMAIN`, `DRAW-REF-FAIL` |

---

## Recommended Next Step

Before building the full pass, run a **feasibility spike** on one known drawing from the TRAVERSE test assembly (PJ00999 / COPY DESIGN TEST 3):

1. Run TRAVERSE as normal.
2. Before the session document cleanup pass, manually call `ReplaceReference` on one known broken drawing view using a small test snippet.
3. Confirm the save succeeds and the view resolves on close+reopen.

This validates the core COM mechanism in your specific Inventor version before investing in the full implementation. The spike takes ~30 minutes and definitively answers whether `ReplaceReference` is viable in your environment before any architectural commitment.

---

## SSA One-Line Verdict

**Build it, but scope it tight:** the drawing repair pass is viable as a post-TRAVERSE phase using `oRenameMap` + `ReplaceReference` + `SilentOperation = True`, provided it only saves drawings where 100% of references resolved, logs all partial failures loudly, and is strictly scoped to drawings referencing models inside the TRAVERSE root.
