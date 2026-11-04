# AA — Strongest Case FOR iProperty Metadata Tagging as Clean Sweeper Reference Map

## The Core Insight: The Files ARE the Database

Vault Copy Design's power comes from its SQL database maintaining a bidirectional reference map. Every file has a GUID, every copy relationship is recorded, every relink is authoritative. The Clean Sweeper currently approximates this with a text RunLog and in-memory dictionaries — both of which are fragile, session-scoped, and external to the files themselves. The iProperty proposal eliminates this fragility by embedding the reference map *inside the files*. The files become their own database. This is not a workaround — it is architecturally equivalent to what Vault does, using the only persistent storage medium the iLogic environment natively owns.

## Problem 1 Solved: Session Death

In-memory dictionaries (`oRenameMap`, `oOldToNew`) die the moment Inventor closes or the rule crashes. The RunLog survives but requires parsing — and if the rule crashes mid-pass, the log may be incomplete. iProperties written to new files in `_CLEAN` survive unconditionally. On any subsequent run, the rule simply opens the files in `_CLEAN`, reads `CS_SourcePath` from each, and rebuilds the entire old→new map in seconds without user input, without reading a log, without a preset form. **Crash recovery becomes automatic.**

## Problem 2 Solved: Drawing Relink Without Preset Map

Currently, the Drawing Copy Mode requires the user to pre-enter 50+ rename pairs. With iProperties on the new files, this becomes a lookup: open the drawing, read its model ref path, open the file at that path, read its `CS_CopyPath` — the new path is right there. Zero manual input. The drawing relink pass becomes fully autonomous for any file that has already been through the traverse. This eliminates the entire preset-map entry burden for repeat runs and second passes.

## Problem 3 Solved: GA-Orphan and Sub-Traverse Discovery

When a drawing references an assembly not in the GA tree, the rule currently has no way to know whether that assembly's sub-tree has already been traversed. With `CS_CopyDate` and `CS_CopyProject` on each copied file, the rule can instantly distinguish: *has this file already been processed in this copy design operation?* One iProperty read answers the question that currently requires a full folder scan and path comparison.

## The Temporary Old-File Tag Is a Feature, Not a Limitation

Old files are not checked out — a Vault sync overwrites any local iProperty change. This sounds like a liability but is actually the perfect safety profile. The tags are *intentionally ephemeral* on the source side. They exist only long enough for the copy operation to complete. There is no Vault pollution, no permanent metadata footprint on originals, no audit trail concern. The tag self-destructs on next sync. Meanwhile, on the new files in `_CLEAN`, the tags persist permanently and become the project's provenance record — who was this file copied from, when, for which project.

## Implementation in iLogic: Trivial

```vb
Dim oProps As PropertySet = oDoc.PropertySets("Inventor User Defined Properties")
' Add or update safely:
On Error Resume Next
oProps.Item("CS_SourcePath").Value = sOldPath
If Err.Number <> 0 Then oProps.Add(sOldPath, "CS_SourcePath")
On Error GoTo 0
```

Read-back is equally simple:
```vb
Dim sSource As String = oProps.Item("CS_SourcePath").Value
```

No external dependencies. No file I/O beyond what the rule already does. No new API surface to learn.

## Downstream: Stripout Pass

A final `CS_Strip` mode iterates every file in `_CLEAN`, removes all `CS_*` properties, and saves. Deliverable is clean of all scaffolding. This is a ~20-line iLogic sub.

## Verdict

This proposal converts the Clean Sweeper's most fragile component — its reference map — from an external, session-scoped artefact into a durable, file-embedded, self-describing structure. It makes every subsequent pass smarter, faster, and fully autonomous. It is the right architecture.
