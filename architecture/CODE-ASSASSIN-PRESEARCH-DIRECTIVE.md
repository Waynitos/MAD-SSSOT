# CODE ASSASSIN / iLogic — Mandatory PRESEARCH Directive

**Status:** APPROVED directive (user instruction, 2026-11-20). **Implementation of enforcement:** PROPOSED until independently tested.  
**Authority:** MAD-SSSOT for Inventor/CLEAN SWEEPER development. BEEXCITED-AI remains authority for any future platform-wide agent protocol.  
**Scope:** All Inventor/iLogic/Vault rule compilation, debugging, changes, and API usage, including CLEAN SWEEPER and Frame Generator.

## Governing platform principle — JUST USE PENCIL

**APPROVED:** [BEEXCITED-AI — JUST USE PENCIL](https://github.com/Waynitos/BEEXCITED-AI/blob/main/architecture/JUST-USE-PENCIL.md) is the platform authority. Before creating or rewriting iLogic code, find a functional existing implementation and test whether it meets the minimum requirement. **Working first; enhancement only for a documented gap or measured benefit.** If audits and patches repeatedly fail to deliver functionality, stop speculative rewrites and return to external and historical search. Preserve source attribution, licence, version compatibility and safety. The NASA pencil anecdote is a metaphor, not historical evidence.

## Mandatory gate: Phase 0 — Web Recon, BEFORE code edits or compilation

1. Identify exact Inventor version, rule, failing API, document types, error message/HRESULT, and current known-working baseline.
2. Search **forums.autodesk.com** first, then **help.autodesk.com**, relevant GitHub code, and other credible technical sources. AI-synthesised responses are discovery leads, not verification.
3. Search internal historical rules, MAD-SSSOT issues, runs, prior experiments and Black Box records before writing replacement logic. Do not reinvent proven functions.
4. Record direct source URL, publication date (where available), author, Inventor version, exact relevant API pattern, prerequisites, warnings, and confidence level.
5. Specifically assess `ReferencedFiles` vs `ReferencedDocumentDescriptors`, `Update2()`, `SaveAs`, `ReplaceReference`, `ComponentOccurrence.Replace`, `DocumentInterests`, Frame Generator, drawing exports, Vault and COM casting whenever relevant.
6. Compare external patterns against the current source. A community pattern is a **candidate**, not automatically approved; confirm its applicability to version, document type, and lifecycle.
7. Prefer the smallest reversible patch, with source preservation and isolated tests. Compilation is not functional verification.
8. Record negative results and failed searches, not only successes. Distinguish PROPOSED, INVESTIGATING, IMPLEMENTED, TESTED, VERIFIED, BLOCKED; for reuse also CODE_REVIEWED, LOCALLY_TESTED, WORKPLACE_VALIDATED, APPROVED.

**No unsearched speculative API rewrite** without documenting why research could not be completed and securing explicit approval for that exception.

## Knowledge preservation — staged deployment

**Now:** Preserve source-linked findings in MAD-SSSOT under existing issues, runs or an indexed research record, without duplicating authoritative sources. Every entry should include problem, original source URL, quoted/minimal pattern, Inventor version, tested rule/commit, evidence/log, failure modes, scope and verification status.

**After Penelope infrastructure is established:** PROPOSED workstream to design a shared searchable Hive knowledge area (GitHub and/or server), with source provenance, deduplication, revision history, and direct links back to original authoritative repositories. Do not claim the shared server or automated retrieval is operational until verified.

**Hive coordination:** Platform-wide agent enforcement, indexing and orchestration proposals should be referenced in BEEXCITED-AI and approved there; MAD-SSSOT retains CLEAN SWEEPER development evidence.

## Initial evidence / caution

- Inventor iLogic COM `E_NOINTERFACE` in recursive traversal: a reported external search exposed relevant type/descriptor distinctions rapidly; actual resolution requires source and runtime verification.
- Frame Generator `SaveAs` E_FAIL: disk-copy + `ReplaceReference` is a research candidate based on user-reported external findings, **not universally proven**; verify document ownership, references, ancestry, API contracts and test logs before adoption.
- Historic working component-replacement rules must be searched and compared before altering CLEAN SWEEPER Phase 3/4.

**Acceptance:** Every new CODE ASSASSIN audit starts with a dated Phase 0 search record containing at least the searched sources/queries and findings or documented no-match, before code changes.
