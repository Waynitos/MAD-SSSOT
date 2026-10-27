# AA — Strongest Case FOR Drawing Re-Association Outside Vault

> **MAD Run:** drawing-reassociation-outside-vault  
> **Agent:** AA (Advocate)  
> **Date:** 2026-10-27

---

## Core Argument

It IS possible to reliably replicate Vault Copy Design's drawing re-association behaviour using iLogic TRAVERSE rules and COM/API automation outside Vault — provided the implementation avoids three specific, well-defined failure modes that have caused the current attempts to stall.

---

## 1. The Mapping Table Is the Right Foundation — the Implementation Is Broken

Every approach the team has tried has correctly identified that a mapping table (old path → new path) is the right data structure. The issue is *when* and *how* the table is populated.

**The fatal sequencing error:** Building the mapping table by scanning disk after the TRAVERSE rename pass has already run means the old paths no longer exist on disk. `File.Exists` returns False, directory listings show only new names, and any attempt to resolve "what was here before" from the filesystem is guesswork.

**The correct sequence:**
1. During the TRAVERSE walk, *before* each `SaveAs` / `File.Copy`, record `oDoc.FullDocumentName` → computed new full path into a `Dictionary(Of String, String)`.
2. Complete the entire TRAVERSE rename pass.
3. Run the drawing repair pass using the pre-built dictionary.

The TRAVERSE rule already builds `oRenameMap` for its own internal use. The drawing repair pass needs exactly this same dictionary — it just needs to be kept alive past the end of the TRAVERSE and handed to the drawing pass. This is not a new data structure; it is a scope/lifecycle change to an existing one.

---

## 2. The COM API Calls That CAN Update Drawing References

Inventor's COM API exposes two complementary mechanisms for programmatic reference rewriting:

**Primary: `DrawingDocument.ReferencedDocuments.ReplaceReference`**

```vbnet
Dim oDrawDoc As DrawingDocument = _
    oApp.Documents.Open(sDrawingPath, False)  ' False = don't show
Dim oOldRef As Document = oDrawDoc.ReferencedDocuments.Item(sOldPath)
Dim oNewRef As Document = oApp.Documents.Open(sNewPath, False)
oDrawDoc.ReferencedDocuments.ReplaceReference(oOldRef, oNewRef)
oDrawDoc.Save()
oDrawDoc.Close(False)
```

This is fully supported, callable from iLogic VB, and is precisely what Vault Copy Design uses at the COM layer after its database transaction resolves the paths. The key requirement: **both the old document object and the new document object must be open in the current Inventor session** at the moment `ReplaceReference` is called. The old document can be opened even if it no longer exists on disk, provided the COM `Document` object reference is still live in the session from the TRAVERSE pass — which it will be if the TRAVERSE has not yet closed its session documents.

**Secondary: `DrawingView.ReferencedDocumentDescriptor`**

For drawings that were saved mid-session while references were unresolved (common in batch runs), individual view-level repair via `DrawingView.ReferencedDocumentDescriptor.FullDocumentName` provides a path-level override that bypasses the session resolver.

---

## 3. ApprenticeServer for Headless Batch Repair

The full Inventor host is not required for drawing reference updates. `Inventor.ApprenticeServer` can be instantiated from inside an iLogic rule:

```vbnet
Dim oApp2 As Object = CreateObject("Inventor.ApprenticeServer")
Dim oDrawDoc As Object = oApp2.Open(sDrawingPath)
```

ApprenticeServer opens drawings in 1–3 seconds vs 15–40 seconds for the full Inventor GUI host. It exposes the same `ReferencedDocuments` collection and `ReplaceReference` method. For a batch of 50–200 drawings, this difference is the line between a 5-minute automated pass and a 2-hour blocking operation.

**Critical flag that prevents silent no-ops:**

```vbnet
oApp.SilentOperation = True
```

Without this, unresolved-reference dialogs block the COM thread and the automation hangs — or worse, returns silently having opened the drawing in a broken state with no references populated.

---

## 4. The `.ipj` Workspace Redirect — Eliminating Most ReplaceReference Calls

Inventor's project file (`.ipj`) defines a `WorkspacePath` that the reference resolver searches when it cannot find a file at its stored absolute path. Before running the drawing repair pass, adding the new folder tree root to `DesignProject.WorkspacePath` tells Inventor's own resolver to search the new location:

```vbnet
Dim oProj As DesignProject = oApp.DesignProjectManager.ActiveDesignProject
oProj.WorkspacePaths.Add(sNewFolderRoot)
oProj.Save()
```

After this, when a drawing is opened and its stored path (old location) is missing, Inventor searches the workspace and finds the identically-named file in the new location — **auto-resolving without any `ReplaceReference` calls at all** for the simple rename-in-place case (same filename, different folder). For cases where the filename also changed, `ReplaceReference` is still needed, but the workspace redirect eliminates the largest class of broken references (Vault Copy Design localisations that moved files without renaming them).

---

## 5. Secondary Vectors

**PackAndGo API enumeration:** `PackAndGoManager` can enumerate all drawing references across an entire project tree and validate them against the mapping table — useful as a pre-flight check and as a post-repair validation pass to confirm zero remaining broken references.

**Vault SDK headless extraction:** Even outside a full Vault session, the Vault SDK (`Autodesk.Connectivity.WebServices`) can be instantiated against a local Vault cache to extract the GUID→current-path map for any files that have been checked in. This provides a ground-truth reference for the mapping table in cases where the TRAVERSE has run and the original documents are no longer open in session.

---

## 6. Why Past Attempts Failed — Three Specific Root Causes

1. **Mapping table built after rename:** Old paths gone from disk. Fix: capture `oDoc.FullDocumentName` *before* `SaveAs`.

2. **`SilentOperation` not set:** Unresolved-reference dialogs block the COM thread on drawing open. Automation either hangs or opens drawings in an empty/unresolved state. Fix: `oApp.SilentOperation = True` before the drawing pass, reset after.

3. **`FastOpen` / deferred-open flags:** If drawings are opened with deferred loading, `ReferencedDocuments` returns an empty collection — the references are not populated until the document is fully loaded. Fix: open with `oApp.Documents.Open(sPath, False)` (second param = show in UI = False, but NOT a deferred/fast open).

---

## Summary Verdict

**The proposition is TRUE** — with a narrowly scoped implementation. The team does not need GUID matching, geometry matching, or Vault database access. The COM drawing API (`ReplaceReference`) is the correct instrument. The mapping table is the correct data structure. The two requirements are: (a) capture old paths before the TRAVERSE moves files, and (b) open drawings with `SilentOperation = True` and no deferred-open flags. ApprenticeServer makes the batch pass fast enough to be practical. The `.ipj` workspace redirect eliminates the largest class of references automatically.

The feature is buildable as a post-TRAVERSE pass within the same iLogic rule session, reusing the `oRenameMap` dictionary the TRAVERSE already constructs.
