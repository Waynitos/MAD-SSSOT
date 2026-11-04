# DA — Strongest Case AGAINST GUID-Based Reference Tracking in the Clean Sweeper

## 1. Inventor doesn't use GUIDs the way Vault does — and that gap is fatal to the premise

The proposal rests on a misreading of how Inventor resolves references locally. Inventor is PATH-FIRST at open time. When an assembly loads, it looks for referenced files by the stored path, then by folder search order defined in the `.ipj` project file. GUID disambiguation is a Vault-layer mechanism that Vault injects into the resolution process via its Inventor integration. Without Vault connected, `ComponentOccurrence.Replace` already works by path — the GUID machinery is simply not in play. Building a GUID-based map to drive `ComponentOccurrence.Replace` is solving a problem that the local Inventor API doesn't have.

## 2. CS_SourcePath already IS the unique identity anchor

No two files in a project share an absolute path. `CS_SourcePath = C:\Vault\PJ00161\...\PJ00161-E3432-8-V0-10-001.iam` is globally unique — it identifies exactly one file, forever, regardless of what anything is renamed to. A GUID adds a second identity token that is functionally identical for disambiguation purposes but requires additional API calls to obtain. The proposal solves an identity problem that CS_SourcePath has already solved, at additional cost.

## 3. Reading source GUIDs requires opening source files — the same O(n) objection the last MAD killed

To read `Document.InternalName` from a source file, it must be open in Inventor. That means opening every source file before copying — the same open/save/close cycle on unchecked-out Vault files that the previous MAD cycle rejected on grounds of Vault state conflicts and cost. The workaround (read the GUID from the new file after SaveAs, then store it as CS_SourceGUID) gives you the new file's old source GUID — but you still need to know which source file each new file corresponds to, which requires CS_SourcePath anyway. GUID becomes a redundant second field derived from information CS_SourcePath already holds.

## 4. `ReferencedDocumentDescriptor` is version-sensitive API surface with no iLogic guarantee

This interface varies across Inventor 2022, 2024, and 2026. Its availability in the iLogic sandbox (which has a restricted API surface compared to full Inventor AddIn development) is not documented as guaranteed. Building the core reference-matching logic on an API that may throw or return nothing on a different Inventor version introduces a fragility that the current path-based `ComponentOccurrence.Replace` approach does not have.

## 5. Duplicate GUIDs from File.Copy are not actually dangerous in this workflow

The concern that `File.Copy` retains the source GUID and causes collisions only matters when both files are visible to the same Vault workspace simultaneously. The Clean Sweeper writes new files to `_CLEAN` — a separate folder. The Inventor project file scopes resolution to that folder. The source files are in a different scoped location. Inventor's path-first resolution finds the right file by folder scope before GUID disambiguation is ever needed. This is not a real collision risk in the Clean Sweeper's controlled two-folder operating context.

## 6. "God-like control" overstates what GUID access gives you in iLogic

Vault's power from GUIDs comes from its SQL database: a live, queryable, bidirectional map of every GUID relationship across every file in every project. iLogic has no database. Reading a GUID from a file gives you one string. Without the database to query against it, that string cannot do what Vault does. You would be building a GUID lookup table in memory — which is exactly what the current `oOldToNew` path dictionary already is, just with paths as keys instead of GUIDs. The underlying data structure is identical; the key type is different; the capability gain is zero.

## Verdict

GUID tracking replicates CS_SourcePath's identity function at higher API cost, requires opening source files the previous MAD cycle already rejected touching, depends on version-sensitive API surface, and solves a collision problem that doesn't exist in the Clean Sweeper's controlled folder context. It is complexity for its own sake.
