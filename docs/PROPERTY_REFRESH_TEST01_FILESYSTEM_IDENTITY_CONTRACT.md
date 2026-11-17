# PROPERTY REFRESH TEST 01 — filesystem identity gate contract (draft v0.1.0)

Scope: isolated `feature/sweeper-v2.2.34-existing-target-repair` only. This document is a **design contract**, not an implemented safety gate or Inventor runtime validation. APPLY remains blocked.

## Independent pure decision contract

`EvaluateApplyIdentity(candidate, projectRoot, protectedRoots, identityEvidence) -> IdentityDecision`

Inputs are immutable records: the candidate's full original path and file type; the approved source project root; explicitly configured Content Center, JC, SJD and other protected external roots; and identity evidence collected by a separate filesystem adapter. Identity evidence must include canonical resolved path, canonical project root, canonical protected roots, and whether resolution succeeded. Lexical normalization is insufficient for APPLY.

Output: `Allowed` boolean (default false), stable reason code, resolved identity, evidence provenance and audit detail. This function must not invoke Inventor, Vault, UI, COM, save, or filesystem writes. It must be shared unchanged by the standalone harness and later integration adapter.

## Fail-closed decision order

1. Reject missing, relative, malformed, non-local, or unresolvable candidate/root paths.
2. Reject unresolved symbolic links, junctions, reparse points, ambiguous aliases, or inconsistent canonical identities.
3. Reject the original/source project tree, even if another path spelling aliases it. Never mutate source files.
4. Reject a candidate outside the explicitly approved *target* project root.
5. Reject a candidate under any protected external library root, using canonical component-boundary ancestry (not string-prefix matching).
6. Allow JC/SJD **filename prefixes** inside the approved project root only when canonical identity establishes they are not inside protected library roots.
7. Reject evidence whose file identity changes between discovery and APPLY; recheck immediately before mutation.
8. Reject any missing/unknown Vault checkout ownership, read-only state, dirty document state, or unresolved COM operation in the subsequent independent mutation gate. A path approval alone never authorizes APPLY.

## Adapter requirements

Filesystem adapter obtains canonical identity using an API capable of resolving Windows junctions/reparse points and aliases; record original and resolved paths and any stable file ID where available. Revalidate at mutation time. No arbitrary timeout can safely abort a blocked in-process Inventor COM call; a watchdog must report a hang and fail the batch without claiming recovery.

## Required regression cases

- Ordinary target part and nested subassembly: eligible identity, subject to all later gates.
- Source-root file: deny.
- External Content Center/JC/SJD library file: deny.
- JC/SJD-named file *within* target project: eligible identity only.
- `C:\\Project\\Target2` must not match `C:\\Project\\Target`.
- Relative path, UNC alias, case variation, dot segments, trailing separators: consistent identity or deny.
- Junction/symlink from target into external library or source: deny.
- Junction/symlink from outside into target: deny unless explicitly approved canonical containment policy is satisfied.
- Unresolvable root, access denied, path disappears, identity changes between checks: deny.
- Dry-run never calls the mutation adapter; APPLY without independently verified Vault checkout ownership and persisted reopen/readback stays blocked.

## Completion evidence

Record each contract test result, VB compile evidence, per-file before/after logs, persisted reopen/readback, and actual Inventor/Vault execution separately. Static source inspection must never be reported as Inventor validation. Do not enable APPLY or publish a completion notification until the shared implementation and both standalone workflows satisfy the full safety contract.
