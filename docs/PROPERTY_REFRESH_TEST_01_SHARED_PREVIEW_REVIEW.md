# PROPERTY REFRESH TEST 01 — read-only assessment and proposed shared preview

Date: 2026-11-14 (Australia/Brisbane).
Status: assessment complete; proposed implementation awaiting G0 approval. NOT QUALIFIED. APPLY BLOCKED.
Repository: Waynitos/MAD-SSSOT.
Required branch: `feature/sweeper-v2.2.34-existing-target-repair`. Never modify or merge main.

## Handover and authorization boundary

The user authorized committing this assessment so agents in other threads can access it. This documentation commit does not authorize implementation, APPLY, checkout, engineering-file modification, merging, production changes or Existing Target Repair work. The next owner must read the authoritative documents, verify live branch state and obtain design approval before implementing.

The original read-only assessment used commit `dd651618e305608cc125ea076d4eedfef70486dd`, matching the remote at that time. Before publishing this handover, a fast-forward pull brought the branch to `7d3d82519c8570b0c93c34c1fbc630ffb253360a`. The checkout was clean before this document was added. No source changes were made by this assessment/publishing task.

## Sources read in full

- `AGENTS.md`
- `docs/BEEXCITED_CODEX_HANDOVER_PROPERTY_REFRESH_01.md`
- `docs/BEEXCITED_CODEX_ROUTING_PROTOCOL.md`
- `docs/PROPERTY_REFRESH_TEST_01_SHARED_CORE_CONTRACT_v0_1.md`
- `docs/PROPERTY_REFRESH_TEST_01_QUALIFICATION_BLOCKERS_20261114.md`
- All five Property Refresh source files under `scripts/ilogic/experiments/`: the standalone TEST_01, Pure, Roots and both historical BBn PROPERTY_REFRESH_ONLY rules.
- All seven original property-refresh regression scripts, supporting review, repository README, scripts README, session startup and iLogic edit protocols.
- Publication refresh: updated main handover, `docs/PROPERTY_REFRESH_01_STATIC_SOURCE_GATE_20261114.md`, updated Pure module and new pure drawing regression, read in full.

The branch-specific AGENTS override supersedes older main-push/conflict instructions. Preserve existing source files, architecture and line endings.

## Verified reusable components and gaps

`BEEXCITED_PropertyRefreshPure.iLogicVb` provides prefix normalization, leading-prefix replacement preserving suffixes, conservative drawing identity checking and typed PropertyChange records. It has no Inventor calls, UI or mutation. Since the original assessment, commit `928bbad` added `PlanExistingDrawingProperty`, which calls the existing drawing planner with named arguments and returns a typed change or Nothing. Reuse this new entry rather than introducing another drawing adapter implementation.

`BEEXCITED_PropertyRefreshRoots.iLogicVb` provides lexical project/approved/protected-root classification, with protected-root precedence and no JC/SJD filename exclusion. It does not resolve actual filesystem identity, reparse points, mapped drives or UNC aliases; it cannot establish ownership or authorize writes.

`BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb` embeds UI, assembly/drawing discovery, property reads, local planning, logging, lifecycle and unreachable mutation code. APPLY returns before discovery. Neither reusable module is connected; ExecutePropertyRefresh is absent. Its project root is the active GA directory, excluding valid sibling project directories. Changes use tab-delimited strings and counts conflate preview candidates with verification.

The historical BBn rules use different scope/mappings, revision resets and APPLY paths. Preserve them as historical experiments; they are not the new core.

The local standalone drawing planner takes filename first, unlike the pure planner's existing-value-first signature. No-change conventions also differ. The new typed drawing entry addresses the adapter ambiguity, but the standalone remains unintegrated. Future callers should use explicit named inputs and the typed result.

Missing: canonical orchestration, RefreshRequest/RefreshReport, read-only adapter, structured FileOutcome/logging, explicit trusted roots and thin wrappers. Authoritative Vault ownership, independent persisted verification and partial-write recovery remain unimplemented.

## Proposed smallest implementation — pending approval

Deliver only a reusable read-only preview path; preserve all original rules.

1. Add one canonical versioned ExecutePropertyRefresh(request, adapter, logger) orchestration entry using the shared-core contract. Reject APPLY before any adapter operation; expose no mutation through the preview adapter.
2. Reuse existing Pure and Roots modules without copied planning/classification logic. Require explicit project, approved and protected roots. Report unresolved physical path identity and ownership as unverified; lexical acceptance is never write permission.
3. One shared Inventor read-only adapter discovers active GA plus recursive IAM/IPT references for assembly entry, or active drawing plus immediate-folder IDW/DWG for drawing entry. Normalize/deduplicate, report failures, guard dirty/read-only/uncertain state and preserve pre-existing user documents. Descriptor traversal and model-state path normalization must follow the edit protocol and be qualified in Inventor.
4. Two thin wrappers own prompts and summaries and call exactly the same core. Model mapping: existing Part Number/SPECIFICATION only. Drawing mapping: existing identity-validated DRAWING_NUMBER only. Preserve revision and issue metadata. No Copy Design dependency.
5. Typed changes/outcomes, phase timings and structured logs. Separate preview, unchanged, skipped and failed counts. Saved/disk-verified/recovery counts stay zero. Unknown ownership must remain explicit even in preview.

Proposed new source files, all under `scripts/ilogic/experiments/`:
- `BEEXCITED_PropertyRefreshCore.iLogicVb`
- `BEEXCITED_PropertyRefreshInventorAdapter.iLogicVb`
- `BEEXCITED_PropertyRefreshAssembly.iLogicVb`
- `BEEXCITED_PropertyRefreshDrawing.iLogicVb`

Proposed supporting changes after approval:
- Add `tests/static/test_property_refresh_shared_preview_contract.py`.
- Correct misleading predicates in existing contract/qualification tests without weakening APPLY qualification. Preserve original-rule regression coverage; the known-blocker assertion in fail_closed currently describes the historical standalone, not a future new wrapper.
- Update `docs/PROPERTY_REFRESH_TEST_01_SHARED_CORE_CONTRACT_v0_1.md` with approved interface, inclusion, flow and acceptance decisions; update this review with evidence.

Packaging issue for design review: the generic edit protocol permits only Imports/AddReference above Sub Main, while the shared-core contract requires iLogic-supported external source inclusion. Document the external library versus executable-rule distinction and a scoped inclusion decision. Do not claim AddVbFile or any packaging approach compatible until compiled in target Inventor. Existing modules already use library structure rather than Sub Main.

Acceptance: both wrappers call one core; no duplicated planner; UI outside core; typed discovery/outcomes; explicit root protection; APPLY rejected; no checkout/property assignment/save operations in preview adapter; actual offline results recorded; no production/main or engineering-file changes. Inclusion and runtime acceptance remain separate G2 evidence.

## Offline evidence

All checks were originally run at dd65161 and rerun at 7d3d825 before publication. Each exact command is `python3 tests/static/<filename>` (run with PYTHONDONTWRITEBYTECODE=1); individual subprocess exit codes were captured. No test fixes were made.

| Filename | Exit | Result at 7d3d825 |
|---|---:|---|
| test_property_refresh_01_contract.py | 1 | 24/25; no-component-replace predicate falsely matches Regex.Replace |
| test_property_refresh_01_drawing_guard.py | 0 | 7 tests |
| test_property_refresh_01_fail_closed.py | 0 | 5 tests |
| test_property_refresh_01_prefix_regression.py | 0 | 16 fixtures; zero failures |
| test_property_refresh_01_qualification.py | 1 | 1/11 assertions; NOT QUALIFIED |
| test_property_refresh_pure_drawing_contract.py | 0 | 3 tests; new since original assessment |
| test_property_refresh_pure_module_contract.py | 0 | 6 tests |
| test_property_refresh_roots_contract.py | 0 | 5 tests |

The qualification gate's apparent Vault pass matches warning text, not an implemented ownership check. Passing source checks and Python mirrors do not execute VB or prove runtime safety. The older static-source-gate document records a different historical source-only inspection; this review records actual Python execution.

Future offline checks can inspect shared calls/inclusion, rejection ordering, mapping restrictions, structured reporting and mutation-API absence. Discovery/path behavior needs fixtures; executable VB tests need a compiler. Python mirrors must remain labelled as reference models.

## Runtime limits and MAD routing

This Linux environment has no dotnet, vbnc, mono or Inventor.exe available. No Inventor compilation/runtime or Vault tests were performed. Inventor 2025 and any actually targeted legacy version need external-inclusion compilation, disposable nested-assembly/drawing preview, reference/model-state handling, property-set/API signatures and document lifecycle validation. Opening documents can have host-side effects and is not proven side-effect-free by source review.

Actual path aliases/reparse handling, Vault identity/current-user checkout/lifecycle/locks, persisted readback, recovery and eventual authorized APPLY require later Windows/Inventor/Vault qualification. Synchronous COM calls cannot be given a hard timeout merely by stopwatch/cooperative cancellation.

This is code inspection and a proposed design, not a completed independent AA -> DA -> SSA validation. Route design review through ChatGPT/MAD; implementation/offline checks through Codex after approval; Inventor/Vault mutation through joint operator review. G0 approval is pending; do not claim G1-G4 qualification. Next owner: reviewer/user to approve or revise this preview-only plan.
