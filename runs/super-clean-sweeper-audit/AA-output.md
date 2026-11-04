## AA: Case FOR Super Clean Sweeper Architecture

### SaveAs(newPath, True) Is the Only Correct Method

`File.Copy` is a filesystem operation. It duplicates bytes on disk but leaves the internal Inventor GUID — the `InternalName` property — identical to the source. The result is two files that Inventor treats as the same document, which breaks Vault's uniqueness guarantees and causes phantom reference resolution conflicts when both copies exist in the same Vault instance. `SaveAs(newPath, True)` is an Inventor API operation: it writes a new file *and* stamps a fresh GUID into the binary. The copy is immediately distinguishable from its parent at the PDM level, not just the filesystem level. For a Copy Design workflow that must coexist with Vault, this is not a preference — it is architecturally mandatory.

### Provenance iProperties Are the Right Persistence Layer

Inventor iProperties travel with the file. They survive moves, renames, Vault check-ins, and re-exports. Writing `CS_SourcePath`, `CS_SourceName`, `CS_CopyProject`, `CS_CopyDate`, and `CS_SourceGUID` directly into each component means the audit trail is embedded in the artifact itself — no external database, no sidecar file, no dependency on a log that can drift out of sync. Any engineer opening a component six months later can inspect its origin without querying any external system. This is the same principle Vault uses for its own lifecycle properties: truth lives in the document.

### CS_SourceGUID Capture-Before-SaveAs Is Provably Correct

`oDoc.InternalName` returns the GUID of the *currently loaded* document. `SaveAs(newPath, True)` generates a new GUID in the copy but does not change the loaded document's GUID. Reading `InternalName` after the `SaveAs` call would still return the original GUID on the original document — but reading it before makes the intent explicit and eliminates any ambiguity about which GUID is being captured. The design is defensive by construction: the source GUID is locked into a local variable before any mutation occurs.

### CS_ModelRefs Enables Fully Autonomous Drawing Relink

An `.idw` or `.dwg` can reference multiple model files. Storing the complete pipe-delimited list of original model paths in `CS_ModelRefs` gives Phase 3 — and any future relink utility — a deterministic input. The drawing does not need to be open during the main walk; the provenance property is a self-contained manifest. Any downstream tool can read `CS_ModelRefs`, resolve each old path against `oActualMap`, and relink with zero guesswork. This design decouples the discovery pass from the relink pass, which means relink can be retried independently without re-running the full tree walk.

### The Skip Guard Is Production-Quality Re-Entrancy

Checking `CS_CopyProject` against the new prefix before processing a file means the rule can be interrupted and restarted without corrupting already-processed files or accumulating duplicate provenance writes. In a large assembly tree where a network hiccup or Inventor stability issue can terminate a run mid-way, re-entrancy is not a nice-to-have — it is what separates a prototype from a deployable tool. The guard also protects against accidental double-runs in Vault workflows where the same rule might be triggered more than once.

### Phase 3 Ref-Rewrite Is Correctly Scoped

Using `oDoc.File.ReferencedFileDescriptors` for the internal reference rewrite is correct because `ReferencedFileDescriptors` operates on the file-level descriptor objects that store the actual path strings Inventor resolves at load time. `ReferencedDocumentDescriptors` operates on in-memory document objects — only valid while the referenced doc is open. Phase 3 opens each new `.iam`/`.ipt`, rewrites its descriptors against `oActualMap`, and saves. This sequence guarantees that every new file's internal pointers are consistent with the new folder structure before Vault ever sees them, making the copied tree self-contained from first check-in.
