# SUPER CLEAN SWEEPER v2.2.34 — Frame Generator research and sprint additions

Status: **research inputs / hypotheses, not validated Autodesk API guidance**. Scope: isolated Existing Target Repair feature branch only. No production/main edits; no Inventor execution claimed.

## User-supplied research references
- Autodesk iLogic Design Copy article: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Copying-an-Inventor-assembly-using-iLogic-Design-Copy.html
- Autodesk forum, Frame Generator copy: https://forums.autodesk.com/t5/inventor-forum/copy-design-made-with-frame-generator/td-p/7028037
- Graitec overview: https://graitec.com/us/blog/ilogic-design-copy/
- CAD Setter Out overview: https://cadsetterout.com/inventor-tutorials/copy-an-autodesk-inventor-design/

## Research hypotheses requiring verification
1. **iLogic Design Copy baseline comparison:** test with all documents closed; determine whether it discovers generated frame members, reference skeletons, and driving master sketches. Verify whether naming rules and Update Part Number are available and how they behave. Check .ipj/Content Center mapping effects.
2. **Frame graph:** inspect actual Inventor 2025 assembly/document descriptors for parent frame, generated members, internal/reference skeletons, master sketch, adaptivity, end treatments, and nested frames. Do **not** assume every frame uses a fixed `Frame0001_Skeleton.ipt` filename or identical folder layout.
3. **Independent copy/relink:** investigate copy ordering (master sketch/skeleton before frame/members) as a hypothesis, not a universal rule. A naive recursive `SaveAs` + `ComponentOccurrence.Replace` may break Frame Generator metadata; test supported APIs and save/replace semantics before considering mutation.
4. **Refresh:** verify the existence, availability, context, and effects of `AFG_Refresh` in Inventor 2025; never assume this command alone repairs links or end treatments.
5. **BOM/iProperties:** compare Part Number, member names and custom properties before/after. Do not automatically force Part Number = filename: existing numbering policies may intentionally differ.
6. **Browser naming:** avoid hard-coded occurrence display names; identify stable document IDs, reference descriptors, and explicit tags where supported.
7. **Folder nesting:** inventory actual generated-member locations and preserve project-relative structure, without assuming one universal folder convention.
8. **Model States/suppression:** investigate limitations and verify supported configurations; do not generalize that Model States never work with Frame Generator.

## v2.2.34 acceptance tests (fail closed)
- Snapshot **forward and reverse references**, including external dependencies, drawings, IPNs, nested frames, generated members, driving sketch, and reference skeleton; block on unknown edges.
- Preview exact source-to-destination mapping, reference changes, iProperties, folder placement and anticipated operations; detect case-insensitive collisions, read-only/Vault ownership issues, unresolved files and changed fingerprints.
- Validate no post-repair references point back to the original design unless explicitly whitelisted and justified; compare before/after graph identities and Frame Generator editability, not just openability.
- Test an already-copied frame with an old skeleton reference, an unchanged nested frame, a checked-out skeleton, missing member, existing destination, and Content Center member.
- Verify frame member edits driven by changing the master sketch; refresh/update should not silently regenerate or overwrite unapproved files.
- Record per-stage timings with existing v2.2.33 profiling checkpoints and failure diagnostics.
- No write phase until authenticated Inventor/Vault evidence, backup/journal, deterministic operation ordering, readback verification, and rollback strategy are implemented and statically checked.

## Sprint implementation order
A. Research actual Inventor 2025 API and iLogic Design Copy behavior; capture reproducible manual baseline.
B. Extend read-only evidence manifest with typed Frame Generator relationships and reverse-reference coverage.
C. Build graph-diff preview and regression fixtures for ghost-skeleton and nested-frame cases.
D. Implement independently verified Vault/read-only preflight, transaction plan and recovery journal.
E. Only then implement guarded reference-changing operations and readback checks; preserve profiler.
F. Validate on **disposable Inventor 2025 copies** with manual signoff; do not describe offline/static checks as Inventor validation.

**Decision:** treat the supplied techniques as investigation leads, not production-ready code. Existing Target Repair must preserve metadata and design intent, not merely relink file paths.
