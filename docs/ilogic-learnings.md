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
