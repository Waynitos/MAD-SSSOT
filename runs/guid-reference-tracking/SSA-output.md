# SSA — Synthesis Verdict: GUID-Based Reference Tracking for Clean Sweeper

**Verdict: Adopt CS_SourceGUID as a stored provenance field on new files. Reject GUID as the primary matching mechanism. Mandate SaveAs over File.Copy unconditionally.**

---

## The Three Questions This MAD Settles

**Q1: Should the Clean Sweeper match occurrences by GUID instead of path?**
No — the DA is correct that Inventor resolves locally by PATH-FIRST. `ComponentOccurrence.Replace` takes a path argument. The GUID layer is Vault's addition to the resolution stack, not a local iLogic primitive. Building a GUID-keyed occurrence matcher in iLogic does not change how `Replace` fires — it just adds a lookup step before the same path-based call. The path map is not being bypassed; it is being dressed up with a GUID key. No practical gain.

**Q2: Should CS_SourceGUID be stored on new files anyway?**
Yes — but for provenance and future-proofing, not for current matching. The AA is correct on one specific point: when a new file is created via SaveAs, Inventor generates a fresh GUID automatically. Reading the OLD GUID before the SaveAs and storing it as `CS_SourceGUID` on the new file costs nothing (file is already open for the SaveAs). It permanently links the new file's identity to the old file's identity in a way that is completely name- and path-independent. This is valuable as a provenance anchor that survives any future rename, folder restructure, or project migration — even if the Clean Sweeper never uses it for matching. It is also the field a future SQLite-backed system (if ever built) would use as its foreign key. Store it; use CS_SourcePath for current matching.

**Q3: Should File.Copy be replaced with SaveAs?**
Yes — unconditionally, and this is the AA's most important finding regardless of GUID tracking. `File.Copy` preserves the original GUID. While this is not an immediate collision risk in the controlled two-folder context (DA correctly notes the project scope separation), it is architecturally wrong and will become a real problem if: (a) the _CLEAN folder is ever added to the same Vault workspace as the source, (b) the Inventor project scopes both folders simultaneously for any reason, or (c) a future tool assumes GUIDs are unique within a workspace. `SaveAs` is the correct operation — it generates a fresh GUID, properly separates the new file's identity from its source, and is what Vault Copy Design does. The rule should use `SaveAs` to the target path rather than `File.Copy` + open. The accuracy goal demands this.

---

## What Changes in the Rule

| Current | Correct |
|---|---|
| `File.Copy(sOldPath, sNewPath)` → open later for relink | `SaveAs(sNewPath)` directly — one operation, fresh GUID, ready for relink |
| No GUID captured | Read `oDoc.InternalName` immediately before `SaveAs` → store as `CS_SourceGUID` in same save |
| Match occurrences by old path string | Match occurrences by old path string (unchanged — this already works) |
| CS_SourcePath alone as identity anchor | CS_SourcePath (operational) + CS_SourceGUID (provenance / future) |

---

## The "God-Like Control" Question

The DA is right that iLogic without a database cannot replicate Vault's GUID power. But the AA is right that `CS_SourceGUID` stored on new files is the portal to that power *when a database is added*. The combination of CS_SourcePath + CS_SourceGUID on every new file means:
- Today: CS_SourcePath drives matching (reliable, proven, path-based)
- Future: if a SQLite companion is added, CS_SourceGUID becomes the foreign key linking the iLogic world to the database world — exactly one field bridges the two
- Always: the new file permanently knows its old identity, independent of any external store

That is not "God-like control" in iLogic alone. It is the foundation that makes God-like control possible when the right tools are added later. Store the GUID now. Use the path now. The GUID earns its keep later.

---

## Implementation Priority

- **SaveAs over File.Copy** — implement now, before next test run. This is a correctness fix, not an enhancement.
- **CS_SourceGUID capture** — implement alongside CS_SourcePath (same save, zero extra cost).
- **GUID-based occurrence matching** — do not implement. CS_SourcePath matching is sufficient and reliable for the current operating context.
