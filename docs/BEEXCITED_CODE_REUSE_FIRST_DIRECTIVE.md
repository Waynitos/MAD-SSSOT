# BEEXCITED CODE REUSE FIRST — MANDATORY ENGINEERING DIRECTIVE

**Status:** Mandatory for all BEEXCITED coding, agents, Code Assassin / iLogic Assassin, MAD reviews, Codex and human-assisted implementation.
**Scope:** Every programming language, repository and project. Applies before drafting a new algorithm, utility, rule or integration.

## Principle
**Find existing wheels that work before building our own.** Prefer proven, compatible code over speculative reinvention. User-supplied previously working rules are first-class evidence. Never claim a source works in our environment until it is actually tested there.

## Required order of operations
1. **Recover prior working evidence.** Search user-provided rules, previous project revisions, repository history, earlier tests and run logs. Ask for a missing specific rule only after trying to retrieve it. Never silently substitute a new implementation for an existing working one.
2. **External prior-art search.** Assign Code Assassin (iLogic Assassin for Inventor) to search official vendor examples, vendor forums with accepted solutions, reputable public repositories, and established community patterns. Record exact URLs, dates/versions when known, API signatures, required setup, known limitations and license/attribution requirements.
3. **Compare before coding.** Build a compact difference matrix: prior working method vs current failing implementation vs sourced proven example. Inspect target document, property-set names, property existence/creation, traversal, document state, setter, update/refresh, save, and failure handling. State a falsifiable hypothesis for each meaningful difference.
4. **Reuse the smallest working mechanism.** Prefer an unchanged proven function or minimal adaptation with documented changes; avoid speculative frameworks, duplicate implementations, new wrappers or architecture unless evidence demands them. Preserve compatibility, safety and source-file boundaries.
5. **Test the smallest unit first.** Isolate a single property on one disposable checked-out file; then a few files; only then full assembly trees/drawing folders. Distinguish static checks, simulation and actual host application tests. Preserve backups and explicit authorization for writes.
6. **Evidence gate.** Every coding proposal/commit must include: links to examples inspected, prior-working source location (or explicitly unavailable), comparison findings, rationale for reuse/adaptation, exact tests actually run, limitations and next real-world test. Do not present untested code as proven.
7. **Stop and escalate** when no suitable example exists, property mapping is unverified, or the original working code cannot be found. State the gap rather than inventing an implementation and calling it qualified.

## iLogic-specific checklist
- Compare `ThisDoc.Document`, `ThisApplication.Documents`, `VisibleDocuments`, `AllReferencedDocuments` and actual target-document identity.
- Check `PropertySets.Item("Design Tracking Properties").Item("Part Number")` and `PropertySets.Item("Inventor User Defined Properties").Item("SPECIFICATION")` against actual file mappings.
- Drawing custom fields vary: never assume `DRAWING_NUMBER` is the title-block field without inspecting a working rule or drawing.
- Separate changing an iProperty from updating a title block; compare `iLogicVb.UpdateWhenDone = True` and document update/refresh where needed.
- Verify existing custom-property behavior vs add-if-missing, dirty/readonly/Vault, save and readback. Keep external libraries unchanged.
- Do not conflate property refresh with Copy Design, renaming, relinking or other Clean Sweeper functions.

## Initial reference examples (research leads, not Inventor-validated)
- Autodesk Community, accepted answer, updating properties of all parts within assembly: https://forums.autodesk.com/t5/inventor-programming-forum/updating-properties-of-all-parts-within-assembly/td-p/10873842
- Autodesk Community, solved, iLogic to update iProperties on all open drawings: https://forums.autodesk.com/t5/inventor-programming-forum/ilogic-to-update-iproperties-on-all-open-drawings/td-p/10556593
- Autodesk Community, changing iProperties with iLogic: https://forums.autodesk.com/t5/inventor-programming-forum/changing-iproperties-with-ilogic/td-p/12352311
- Autodesk Community, title block update from iLogic (accepted update-when-done suggestion): https://forums.autodesk.com/t5/inventor-programming-forum/title-block-update-from-ilogic/td-p/7891019
- Autodesk University, iLogic rule to get the job done (traversal and Part Number example): https://static.au-uw2-prd.autodesk.com/Class_Handout_MFG321077_Lauren_Ames.pdf

## Enforcement
This directive is a pre-coding gate, not an optional research appendix. For every future coding task, cite this document in the implementation handoff and document completion of the prior-art comparison **before** writing new code. If skipped, mark the implementation process noncompliant and return to research.
