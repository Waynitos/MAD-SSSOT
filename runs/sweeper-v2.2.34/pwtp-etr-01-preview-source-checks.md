# PWTP-ETR-01 — preview-only source gate

**Status: IMPLEMENTED (experimental), NOT TESTED in Inventor, NOT a complete v2.2.34 candidate.**

Commit: `fe58bb271cb15d74a8e9eb7d6dc556229bc93efe`.
Rule: `scripts/ilogic/experiments/ETR_PREVIEW_ONLY_PWTP01.iLogicVb`.

## Purpose
Collect the referenced document graph from a copied target assembly without altering Inventor documents. Output is a TSV under the OS temporary directory (`SCS_ETR_Preview`). Record file existence, filesystem read-only flag, and reference inspection failures.

## Static source checks performed before commit
- No `.Save(`, `.Save2(`, `.SaveAs(`, `ReplaceReference(`, `SetAttributes(` or `File.Copy(` calls in experimental source.
- Explicit PREVIEW_ONLY marker and missing-reference diagnostics.
- Vault checkout status always UNKNOWN rather than inferred from read-only attribute.
- Depth guard (100) and visited-path cycle guard.
- All seven checks passed via source-string assertions in development session.

## Known limits
- `ReferencedDocuments` enumerates document-level dependencies, **not occurrence-level paths or all unresolved descriptor links**; it may load referenced documents. A complete repair preview needs `ReferencedDocumentDescriptors`, occurrence paths, source/target provenance, and explicit old/new mapping.
- Existing source read-only state does not establish Vault checkout or effective write permission.
- Frame Generator detection and associativity verification are **not implemented** in this preview.
- No repair, rollback, collision handling, save/reopen verification or performance profiler is implemented in this experimental file.
- Source assertions are not a VB/iLogic compiler, Inventor API runtime test, or regression suite.
- Source version and main branch unchanged.

## Next experiment
Build a descriptor- and occurrence-aware preview against a disposable copied frame with explicit expected target paths. Verify completeness of old references before allowing any mutation. Then design transactional repair with backup, journal, save verification, and fail-closed Vault preflight. Retain v2.2.33 profiling in the eventual integrated rule.

**Promotion gate:** do not call v2.2.34 ready until complete candidate source and static checks are committed, with Inventor runtime tests explicitly outstanding.
