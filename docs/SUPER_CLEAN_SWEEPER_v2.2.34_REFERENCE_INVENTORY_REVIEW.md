# v2.2.34 reference inventory experiment — source-level review (2026-11-11)

Branch: feature/sweeper-v2.2.34-existing-target-repair. Parent: v2.2.33 profiler. Experiment commit: 455c27e3635600fbf505d2005e115ba50bb28a78.

## Scope and static inspection
- New standalone iLogic diagnostic only; existing sweeper source, mode selector, profiling and production/main remain unchanged.
- Walks the active copied GA and reachable in-root model documents through Inventor DocumentDescriptor references; reports path and parent relationships.
- Explicitly reports missing, external and descriptor failures, plus a blocking count. Writes only a diagnostic TXT file to the OS temporary directory.
- No File.Move, Save, SaveAs, ReplaceReference, Vault state changes or file-attribute mutation in the experiment.
- Uses a case-insensitive visited set to prevent cycles; path-root check requires a directory separator to avoid false matches from sibling folders sharing a prefix.
- Read-only is with respect to document files: descriptor.ReferencedDocument can cause Inventor to resolve/load documents into memory; it is not a zero-side-effect filesystem-only scan.

## Known limitations / DA findings
1. **Not an executable repair candidate.** No rename plan, preview approval, safe reference replacement, rollback, or post-repair reopen verification.
2. **Frame Generator is not proven safe.** Skeleton, derived references, adaptive/linked geometry and member ownership must be inventor-tested separately; generic descriptors alone cannot establish all semantic dependencies.
3. **External dependencies are recorded but not traversed.** A file outside the root is a blocking finding; no modification is permitted.
4. **Drawings and IPNs are not discovered by reverse reference search.** They must be explicitly enumerated and checked before any mutation.
5. **Vault ownership, checkout, read-only, collisions, unresolved references and duplicate target names are not evaluated by this experiment.** Any eventual mutation must fail closed.
6. **Potential API compatibility:** DocumentDescriptor.FullDocumentName / ReferencedDocument and late-bound behavior must be compiled in the target Inventor/iLogic version. Descriptor failures are reported, not silently ignored.
7. **Path handling:** report output is not escaped for pipe/newline characters; this is a human diagnostic, not a stable machine parser. Root is the GA directory, which may be narrower than the selected target project root.
8. **Performance:** in-memory descriptor traversal may load many files; measure discovery time and loaded-document counts during isolated tests. v2.2.33 profiling remains in the unchanged parent rule.

## Review verdict
Static manual review: diagnostic is non-mutating to CAD files by inspection. **No Inventor compile or runtime testing performed.** Not approved for production, not safe to use as proof of reference integrity, and not ready to notify as a complete v2.2.34 repair candidate.

## Next gate
Build explicit target-root selection, complete dependency inventory including drawings/IPNs/Frame Generator, collision and Vault fail-closed preview, then a transactional Inventor-supported reference update with backup and reopen verification. Preserve the v2.2.33 profiler checkpoints.
