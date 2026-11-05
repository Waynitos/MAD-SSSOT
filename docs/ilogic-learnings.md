# iLogic Learnings

## Drawing model references — use ReferencedDocumentDescriptors

When reading model references from a DrawingDocument, use `ReferencedDocumentDescriptors`, not `ReferencedFileDescriptors` or `ReferencedDocuments`.

- `ReferencedDocuments` silently omits DART SHUT refs (models present in the drawing but in an unloaded/shutdown state).
- `ReferencedFileDescriptors` can also miss them.
- `ReferencedDocumentDescriptors` returns all of them.

Strip any DART state tag from the path before using it:
```
path.iam<DART SHUT>  →  path.iam
```
```vb
Dim sRef As String = oDesc.FullDocumentName
Dim iAngle As Integer = sRef.IndexOf("<"c)
If iAngle > 0 Then sRef = sRef.Substring(0, iAngle)
```

Fall back to `ReferencedDocuments` only if the descriptor loop throws. Do not fall back just because the descriptor loop returned no models.

This was the cause of "Open the top-level GA assembly first" when Super Clean Sweeper was started from a drawing that had DART-shut model refs. Fixed in v2.2.20.

## Phase 1 rename map — prefer file-level walks; cache CS_* property reads

Phase 1’s main cost on reruns is not `WalkTree` recursion. It is full `Documents.Open` calls in `ReadCSSourcePath` and `IsAlreadyProcessed` (often ~2 opens per existing target) just to read `CS_SourcePath` / `CS_CopyProject`.

For building the old→new file list without opening every document:
- Prefer `Document.File.AllReferencedFiles` (flat, deduplicated) or recursive `File.ReferencedFileDescriptors` → `ReferencedFile`.
- These list suppressed / unloaded references without `Documents.Open`. `AllReferencedDocuments` only lists loaded documents and can miss DART SHUT / suppressed refs.
- Guard with `FileDescriptor.ReferenceMissing` and skip `ReferencedFileType = kForeignFileType` before following `FD.ReferencedFile`.
- Keep Content Center filtering path-based (`"CONTENT CENTER"` in path) unless you truly need `IsContentMember` (that still requires a document open).

Property-read win (keep WalkTree shape or switch walk):
- Merge `IsAlreadyProcessed` + `ReadCSSourcePath` into one cached open that reads both `CS_CopyProject` and `CS_SourcePath` once per target path.
- Or write a source→target sidecar (CSV/JSON) each run so Phase 1 resolves reuse/collisions from the manifest + `File.Exists`, and only opens a file when the manifest is missing or disagrees.

Apprentice `FileSaveAs.AddFileToSave` + `ExecuteSaveCopyAs` is the fastest public copy-design pattern, but it runs out of process, skips files that need migration, and does not handle drawings — not a drop-in for in-process Super Clean Sweeper.

Drawing discovery/relink stays separate: assembly→model walks do not find `.idw`/`.dwg` files.

Sources (research 2026-11-05):
- https://forums.autodesk.com/t5/inventor-programming-ilogic/difference-between-referencedfiledescriptors-and/td-p/11594168
- https://forums.autodesk.com/t5/inventor-programming-ilogic/ilogic-check-for-and-delete-all-unresolved-components/td-p/8195212
- https://forums.autodesk.com/t5/inventor-programming-forum/looking-for-a-filesaveas-object-primer/td-p/3091750
- https://forums.autodesk.com/t5/inventor-programming-forum/apprentice-server-with-powershell-working-prefix-copy-design/td-p/13750480
- https://forums.autodesk.com/t5/inventor-programming-forum/access-parent-to-set-reference/td-p/12425676

## Phase 2 SaveAs — one write; SaveCopyAs keeps InternalName

Phase 2’s main cost is not `SaveAs` itself. It is open → `SaveAs(path, True)` → reopen the copy → write CS_* / activate design view → `Save2` → close (often 2–3 opens and 2 disk writes per file), plus any `IsAlreadyProcessed` open of the target.

SaveCopyAs identity:
- Autodesk’s `FileDescriptor.ReplaceReference` docs state documents copied with Save Copy As (or Explorer copy) keep the same InternalName.
- Do not treat `SaveAs(…, True)` output as a “new GUID”. That shared InternalName is why `ReplaceReference` works on the copy.
- The only documented API to assign a new internal name is `PutInternalNameAndRevisionId`, and only on a New or SaveCopyAs document that has not yet been saved (needs a live Inventor test before relying on it). Forcing new InternalNames could break Phase 3 relink.

Faster in-process pattern:
- Write CS_* props and activate the design view on the in-memory source *before* `SaveAs(new, True)`, then close the source without saving so the copy gets one write.
- Prefer documents already loaded under the open top assembly (`AllReferencedDocuments`) over `Documents.Open` per file when safe for your DART SHUT / unloaded-ref rules.
- Prefer `FileDescriptor.ReplaceReference` with an old→new map over per-occurrence relink when possible.
- Keep `File.Copy` / `FileManager.CopyFile` as fallback only: file-system copies do not reset Part Number the way SaveAs does. `ReplaceReference` clears adaptivity — use `Replace2` + `LocalAdaptive=True` when needed.

Apprentice `FileSaveAs.ExecuteSaveCopyAs` remains the fastest batch copy but stays out of process and does not replace drawing relink.

Sources (research 2026-11-05):
- https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/FileDescriptor_ReplaceReference.htm
- https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/AssemblyDocument_PutInternalNameAndRevisionId.htm
- https://forums.autodesk.com/t5/inventor-programming-forum/trying-to-save-and-replace-parts-in-an-assembly/td-p/11088412
- https://forums.autodesk.com/t5/inventor-programming-forum/assembly-and-some-of-its-parts-renamed-and-saved-as-new-copy/td-p/11984657
- https://forums.autodesk.com/t5/inventor-programming-forum/vba-filedescriptor-replacereference-clears-adaptivity/td-p/11142067
- https://forums.autodesk.com/t5/inventor-programming-forum/ilogic-design-copy-programatically/td-p/5796804

## Phase 3/4 ref rewrite — Prefer ReplaceReference-only; drop duplicate occurrence passes

Phase 3a’s file-level `FileDescriptor.ReplaceReference` already rewrites refs across the structure. Phase 3b (occurrence `Replace`) and Phase 4 (`Phase4_WalkOccs`) mostly reload children and repeat the same work; Phase 4 also `Save2`s every target assembly with no dirty check and can save the GA twice.

Prefer:
- Keep 3a as the only bulk pass. Run occurrence replace only for locked/E_INVALIDARG descriptors and adaptive occurrences (`Replace2(path, False, , True)` then `LocalAdaptive = True`). `ReplaceReference` alone clears adaptivity.
- Bottom-up order must come from the rename/dependency map. Sorting by path length is not deepest-first when all targets sit in one flat folder.
- Make Phase 4 check-only: scan `File.ReferencedFileDescriptors` without forcing `oOcc.Definition.Document` loads or unsuppress storms; open/replace only when a stale ref remains; save only if `Dirty`; open the GA invisible when possible.
- Buffer log writes (`StringBuilder`) instead of per-reference `File.AppendAllText`.

Risks: shared InternalName is required for `ReplaceReference`; basename fallbacks can point at the wrong file; model states/substitutes need their own descriptor handling; in-memory docs can look stale after replace until reload/model-state toggle.

Sources (research 2026-11-05):
- https://forums.autodesk.com/t5/inventor-programming-forum/trying-to-save-and-replace-parts-in-an-assembly/td-p/11088412
- https://forums.autodesk.com/t5/inventor-programming-forum/vba-filedescriptor-replacereference-clears-adaptivity/td-p/11142067
- https://forums.autodesk.com/t5/inventor-programming-ilogic/replace-part-in-assembly/td-p/2557686
- https://forums.autodesk.com/t5/inventor-programming-forum/assembly-and-some-of-its-parts-renamed-and-saved-as-new-copy/td-p/11984657
- https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/FileDescriptor_ReplaceReference.htm
- https://forums.autodesk.com/t5/inventor-programming-forum/replacereference-on-quot-piping-runs-environment-quot-assembly/td-p/6392875
