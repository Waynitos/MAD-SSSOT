# AA — Strongest Case FOR GUID-Based Reference Tracking in the Clean Sweeper

## GUIDs are what Inventor actually uses. Paths are a convenience fiction.

When an assembly occurrence references a sub-component, Inventor does not bind it by file path. It binds it by `Document.InternalName` — a GUID baked into the file's binary structure at creation time. The path stored alongside it is a *resolution hint* — the first place Inventor looks when it needs to open the file. If the path is wrong or the file has moved, Inventor falls back to a GUID search across the project's known library paths. The GUID is the truth. The path is best-effort.

The Clean Sweeper's entire current architecture is built on the convenience fiction. It tracks old path → new path, matches occurrences by path comparison, and fails the moment a path changes, a file appears in an unexpected location, or session state is lost. Every one of the failure modes documented in this project — missed relinks, GA-orphan subs, JC file parent gaps — traces back to path matching being unable to unambiguously resolve identity. GUID matching eliminates every one of them.

## The operative API is `ComponentOccurrence.ReferencedDocumentDescriptor`

This property returns a `DocumentDescriptor` whose `InternalName` is the GUID the occurrence is actually bound to — not the path it resolved to, not the filename, but the raw identity token. With this, the matching algorithm becomes:

```vb
Dim sOccGUID As String = oOcc.ReferencedDocumentDescriptor.InternalName
If oOldGUIDToNewPath.ContainsKey(sOccGUID) Then
    oOcc.Replace(oOldGUIDToNewPath(sOccGUID), True)
End If
```

This is name-agnostic. Path-agnostic. It does not matter what the old file was called, what folder it lived in, or what the new file is called. If the occurrence's bound GUID matches a key in the map, the replacement fires. This is *exactly* how Vault Copy Design works — and it is why Vault never misses a relink.

## `CS_SourceGUID` on the new file is the permanent portal

When a new file is created via `SaveAs`, Inventor assigns it a fresh `InternalName`. The old GUID is gone from the file — but we capture it first and write it as `CS_SourceGUID` to the new file's iProperties. Now:

- Given any new file in `_CLEAN`: read `CS_SourceGUID` → know exactly which old occurrence it replaces
- Given any assembly occurrence: read its bound GUID → look it up in a map built from `CS_SourceGUID` values → find the new file → replace
- The map rebuilds from the files themselves on any subsequent pass, crash recovery, or session restart — no RunLog parsing, no user input, no memory of prior sessions required

This is "God-like control" in the precise sense: identity is preserved across every rename, every move, every session boundary. The old GUID is the immutable token that links every occurrence in every assembly and drawing to its correct new replacement, forever, regardless of what either file is named or where it lives.

## `File.Copy` is architecturally wrong. `SaveAs` is the only correct operation.

`File.Copy` duplicates the binary — including the GUID. The copy and the original now share an identity. Vault sees two files as the same entity. Inventor's project resolution can resolve to either, non-deterministically. The current rule's use of `File.Copy` for speed creates a silent identity collision that can cause Inventor to open the wrong file when paths are ambiguous. `SaveAs` is the only operation that generates a fresh GUID, correctly separating the new file's identity from its origin. Switching to `SaveAs`-based copying is not optional — it is the prerequisite for GUID-based tracking to work, and it is independently the correct operation regardless.

## Verdict

GUID-based tracking via `Document.InternalName` + `ComponentOccurrence.ReferencedDocumentDescriptor` + `CS_SourceGUID` iProperty is not an enhancement to the current architecture. It is the architecture Vault uses, now available to the Clean Sweeper. It eliminates path-matching fragility entirely and makes the system as robust as Vault Copy Design at the reference layer.
