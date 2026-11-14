# BEEXCITED / MAD-SSSOT — Codex Handover: PROPERTY REFRESH TEST 01
Date: 2026-11-14
Status: DEVELOPMENT HANDOVER; NOT RUNTIME-VERIFIED; APPLY NOT APPROVED
Repository: Waynitos/MAD-SSSOT
Mandatory branch: feature/sweeper-v2.2.34-existing-target-repair
Never modify or merge to main.

## Background and desired architecture
Clean Sweeper is a complex Inventor Copy Design/renaming/reference-repair workflow. Property Refresh must first be isolated as a robust standalone tool, independent of Copy Design, then become one reusable BEEXCITED iLogic Function Library component. The same canonical implementation must serve the standalone test and later Clean Sweeper/SQL adapters; no rewritten duplicates. Keep Indexer / Copy Planner / Executor and Existing Target Repair work separate.

## Authoritative documents (read full files)
- AGENTS.md (branch override is critical)
- docs/PROPERTY_REFRESH_TEST_01_SHARED_CORE_CONTRACT_v0_1.md
- docs/PROPERTY_REFRESH_TEST_01_QUALIFICATION_BLOCKERS_20261114.md
- docs/BEEXCITED_CODEX_ROUTING_PROTOCOL.md
- scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb
- scripts/ilogic/experiments/BEEXCITED_PropertyRefreshPure.iLogicVb (verify path and current source)
- existing root-classification module (discover actual filename via repository search)
- tests/static/test_property_refresh_01_contract.py
- tests/static/test_property_refresh_01_qualification.py
- tests/static/test_property_refresh_01_prefix_regression.py
- tests/static/test_property_refresh_01_drawing_guard.py
- other property-refresh tests (discover actual paths)
Some files may have changed since this snapshot; verify paths and current Git history. Do not assume a previous report proves code is still in that state.

## Entry workflows
1. Active GA .iam: prompt once for new PJ##### prefix; recursively discover nested .iam/.ipt, deduplicate, include GA, plan Design Tracking Part Number and existing custom SPECIFICATION leading-prefix replacement preserving suffix; other populated fields only if mapping is explicitly approved.
2. Active GA .idw/.dwg: prompt for PJ#####; include active drawing and other .idw/.dwg in its immediate folder only; conservative existing DRAWING_NUMBER identity validation; preserve existing suffix; never reset revision or issue metadata.

## Non-negotiable safety
- Dry-run preview default, explicit APPLY confirmation but APPLY remains BLOCKED pending qualification.
- Explicit trusted project root and approved writable roots; external Content Center, JC, SJD protected by resolved path, not filename. In-project JC/SJD copies may be eligible subject to ownership.
- Source files and external libraries never modified. No automatic checkout.
- Vault ownership must be authoritatively verified; filesystem writable alone is insufficient. Dirty, read-only, locked and uncertain files fail closed.
- Typed property change records, structured per-file outcomes, logs, separate preview/saved/disk-verified counts.
- On future APPLY: preflight, save once, independent persisted readback, rollback or RECOVERY_REQUIRED; never claim COM hard timeout.
- No Inventor/Vault runtime testing claim without actual Windows Inventor/Vault execution.

## Known status and blockers
Existing standalone candidate historically embedded traversal/planning/mutation and blocks APPLY. A pure planning component and a read-only root classifier have been committed in previous development. Their integration into one callable shared core, authoritative Vault check, independent disk verification, recovery and wrappers remain unqualified. Historical static tests may only check source tokens. Confirm live status before edits.

## FIRST CODEX TASK — bounded pilot
Read-only preflight: inspect full current sources, discover all property-refresh files and test commands, identify conflicts with existing AGENTS.md. Produce concise implementation plan and exact file list. Then, if approved to implement, extract/connect the canonical shared **read-only preview** core and thin assembly/drawing entry wrappers using the existing pure planner and root classifier unchanged where practical. Keep APPLY blocked. Do not touch Existing Target Repair or main. Avoid speculative Inventor API calls; mark unverified assumptions.

## Acceptance evidence
- One canonical shared implementation with documented public interface/version, not duplicated across wrappers.
- Both entry workflows call same core; UI prompts live outside core.
- Read-only discovery, eligibility and property planning have typed outputs and structured logs.
- External library and project-root safeguards explicit and testable.
- Offline tests actually run with commands, exit status and regression results; failed tests and limitations recorded.
- Git diff reviewed for truncation and unintended files; a reviewable branch commit/PR.
- Explicit statement: Inventor compilation and runtime testing still required; APPLY not enabled.

## Human acceptance sequence
G0 design reviewed → G1 offline pure/static regression evidence → G2 Inventor compilation and disposable preview → G3 Vault-authorized APPLY with persisted readback/recovery → G4 regression qualification and reuse approval. Do not skip gates.

## Codex task starter
Read AGENTS.md and this handover; verify current branch, sources and tests. Start with read-only preflight and an implementation plan for shared preview core + two thin wrappers. Do not modify main, enable APPLY, auto-checkout, merge or claim Inventor testing. Report exact proposed files, risks and test commands before writing.


## 2026-11-14 source-level integration hazard (verified by full source inspection)
The existing standalone rule calls its **local** `PlanDrawingNumber(filenameStem, existingNumber, targetPrefix)` with filename first, whereas the separate pure module exposes `PlanDrawingNumber(existingValue, fileBaseName, proposed)` with existing property first. Their argument order is reversed. A direct replacement without an explicit named adapter would silently mis-map values; because both parameters are String, compilation would not detect it. Their no-change contracts also differ: the standalone returns empty String as a skip sentinel; the pure module returns the original existing value. The pure module also returns original value when the old prefix is not proven, while the standalone only queues changes if the proposed value is nonempty. Before wiring wrappers, establish a single typed drawing planning contract, explicit named arguments or request object, and tests for mismatch, unchanged/idempotence, missing value, suffix preservation, filename mismatch and lower-case old prefix. This finding is based on source inspection only; it is not a runtime failure claim.

The current standalone still includes an unreachable APPLY mutation block after an explicit early APPLY rejection. Do not interpret the presence of `Save2(False)` or in-memory readback as qualification. Keep APPLY fail-closed and remove/defer mutation logic only as part of a reviewed refactor; do not activate it.

The standalone's `root` is the active document's directory, not a trusted project root, so its current eligibility gate excludes valid sibling project directories and has no authoritative external-library root mapping. Do not weaken containment; use the existing root-classification work and explicit ownership inputs.
