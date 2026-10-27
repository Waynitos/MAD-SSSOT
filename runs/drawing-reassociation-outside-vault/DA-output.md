# DA — Strongest Case AGAINST Drawing Re-Association Outside Vault

> **MAD Run:** drawing-reassociation-outside-vault  
> **Agent:** DA (Devil's Advocate)  
> **Date:** 2026-10-27

---

## Core Argument

It is NOT reliably possible to replicate Vault Copy Design's drawing re-association using iLogic TRAVERSE rules and COM/API automation outside Vault. The team is attempting to bridge a categorical architectural difference using file-layer tools against a problem that is solved at the database layer. The result is not merely imperfect — it is actively hazardous.

---

## 1. Vault Copy Design Is a Database Transaction, Not a File Operation

The fundamental error is treating Vault Copy Design as a sophisticated file-copy-and-rename tool. It is not. It is a **transactional database operation** that produces files as a side effect.

When Vault executes a Copy Design, every file object in the Vault database receives a new entity record with a new Vault ID. The internal cross-reference map — which drawing view points to which model, which positional representation, which sheet metal flat pattern state — is rebuilt **atomically from the database's own relational schema**. The drawing's reference update is not performed by reading a path string and replacing it. The Vault server resolves entity-to-entity relationships that were cloned together in the same transaction. The drawing never "knows" the old path. The database resolves the relationship, then materialises the updated `.idw` with correct references already written.

An iLogic rule operating outside Vault has zero access to this relational layer. It sees files. Vault sees objects in a version-controlled relational store with full dependency graphs. These are categorically different things, and no amount of COM sophistication bridges that gap.

---

## 2. The Mapping Table Fails on Real Assembly Trees

The mapping-table approach sounds tractable on a simple linear assembly. Real engineering assemblies immediately expose its limits.

**Multi-use components** are the first failure. A standard hardware component — a bolt, a bracket, a seal — may appear in dozens of subassemblies across the tree. The mapping table gives it one new path. But the drawing BOM may reference that component's iProperties from three different configuration contexts. After remapping, all three point to the same new file. Two of those references may be silently wrong — pointing to the correct file but the wrong configuration or positional representation.

**Shared references across project boundaries** are the second. If a subassembly in the tree is also referenced by a GA assembly outside the copied tree, renaming it breaks the other assembly. The mapping table has no way to know the component's reference scope. The TRAVERSE rule walks one root; the damage extends to everything that shared the component.

**In-place features** are fatal. Parts modelled in-place store positional and geometric constraints back to the parent assembly context. When the parent is renamed, the in-place part's adaptive references point to a path that no longer exists. The mapping table can update the file link but cannot reconstruct the adaptive relationship.

**Variant naming collisions** occur when the naming convention produces the same candidate new name for two distinct old paths. The mapping table has no tiebreaker and produces a corrupt entry.

---

## 3. GUIDs After File Copy Are Not the Discriminating Signal You Need

Inventor embeds internal document GUIDs in `.ipt`, `.iam`, and `.idw` files. The seductive premise is: copy files, GUIDs are preserved, match on GUID.

This is wrong in two ways. First, **Vault Copy Design explicitly regenerates GUIDs** for every copied file as part of its transaction — the whole point is to produce a distinct document set. If you copy files outside Vault, the copies retain the source GUIDs. You now have two files on disk with identical GUIDs. Inventor's reference resolution uses path as its tiebreaker. GUID matching provides no additional discriminating power.

Second, when the TRAVERSE renames a file, the GUID does not change — but the path does. Any drawing that referenced the old path by GUID-plus-path now has a broken path with a GUID that matches a file at a different location. The COM API's `ReferencedDocuments` collection reports the reference as unresolved. There is no COM method to say "find the document with this GUID wherever it is and update this reference to its current path." Inventor's resolver does not expose that mechanism outside of Vault.

---

## 4. Geometry Matching Is Computationally and Logically Infeasible

Geometry hashing as a fallback fails for structural families specifically — which are exactly the files most likely to be renamed and relocated by a Copy Design workflow.

A 100mm RHS and a 150mm RHS have different geometry. A 100×6mm RHS and a 100×5mm RHS hash very similarly under any coarse volumetric metric. Mirrored parts have identical surface area, volume, and bounding box. The geometry-based approach is least reliable precisely where it is most needed.

Even if the accuracy were sufficient, the computational cost is prohibitive. Fully loading every candidate `.ipt` via `DocumentManager.Open` to compute a geometry hash, against an assembly with hundreds of unique parts, takes tens of minutes while holding Inventor's single-threaded COM host. This is not a viable background operation.

---

## 5. The COM API Cannot Rewrite References on Closed/Unresolved Drawings

`DrawingDocument.ReferencedDocuments` — the property the AA argument relies on — is **read-only for unresolved references**. You cannot programmatically say "this broken reference should point to this new path" when the model file is not open and loaded in the current Inventor session.

To rewrite a drawing's model references you must:
1. Open the drawing in Inventor → triggers reference resolution → may immediately throw an unresolved-reference dialog blocking automation
2. Open all referenced model documents in the same session
3. Perform the reference replacement
4. Save

Step 1 is already broken. When TRAVERSE has finished and drawings still reference old paths, opening a drawing prompts the user to locate missing files. COM automation can suppress or redirect this dialog, but suppression means Inventor opens the drawing with **unresolved views** — at which point the views are in an indeterminate state. Programmatic reference replacement on an unresolved drawing view is not a supported operation. The API throws errors or silently does nothing.

Even when models are open, `DrawingView.ReferencedFile` and related properties are not writable through the public COM interface. Inventor's reference integrity system requires updates to go through its internal resolver, which performs constraint and configuration validation not exposed to external COM callers.

---

## 6. A Partial Solution Is More Dangerous Than No Solution

This is the decisive argument. If re-association succeeds on 90% of views and silently fails on 10%, the result is a drawing set that **appears correct**. Title blocks show the right project code. The first-page view resolves. The BOM renders. A draftsman reviewing the output has no practical means to know that three detail views in sheet 4 still point at the original pre-copy source parts.

This is not a theoretical failure mode — it is the guaranteed outcome of any path-based COM rewriting approach applied to a real assembly tree with shared components, because shared components will produce mapping table collisions or out-of-scope references the automation cannot resolve. Those views will silently load from the wrong model. The drawing will pass review, approval, and issue with incorrect geometry depicted.

Vault Copy Design's value is not merely that it updates references. It is that it updates them **transactionally and completely, or not at all**. There is no partial state. An iLogic COM approach has no transaction boundary by design. It produces partial states.

---

## Summary Verdict

**The proposition is false.** Vault Copy Design's drawing re-association is not replicable outside Vault because it is a database-layer operation, not a file-layer operation. The mapping-table approach fails on multi-use components, shared references, and in-place features. GUID matching fails because Copy Design regenerates GUIDs while file renaming preserves them, producing an unresolvable collision. Geometry matching is computationally infeasible and logically unreliable for structural families. The COM API cannot rewrite references on unresolved drawings. Most critically, any partial implementation produces drawing sets that appear correct while containing silent reference mismatches — measurably worse than leaving drawings visibly broken.

Drawing re-association must remain within Vault's managed environment. Any out-of-Vault automation should scope itself strictly to model file operations and explicitly disclaim responsibility for drawing reference integrity.
