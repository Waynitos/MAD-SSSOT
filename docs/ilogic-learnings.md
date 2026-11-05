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
