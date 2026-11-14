# PROPERTY REFRESH TEST 01 — Shared-core implementation gate

Status: DESIGN CONTRACT ONLY / NOT INVENTOR-VALIDATED / APPLY BLOCKED
Scope: isolated `feature/sweeper-v2.2.34-existing-target-repair` branch; no production or Existing Target Repair implementation changes.

## Non-negotiable architecture

One versioned canonical core must be called **unchanged** by (a) assembly standalone wrapper, (b) drawing standalone wrapper, (c) offline test harness and (d) later Clean Sweeper adapter. Wrappers may gather inputs, display UI and translate Inventor document/property APIs, but must not reimplement prefix or drawing-identity planning. The core must run without Copy Design and without UI.

Separate contracts:
- **Discovery**: input active document + explicit scope; output deduplicated normalized path/identity manifest and per-edge traversal evidence. Assembly: include active GA and recursively referenced .iam/.ipt; drawing: active .idw/.dwg and same-folder .idw/.dwg. Abort on incomplete traversal rather than presenting a complete manifest.
- **Ownership/eligibility**: input manifest entry, explicitly confirmed old-project root, trusted external library roots and Vault state; output ALLOW/SKIP/BLOCK with reason. Canonicalized containment must use directory boundaries and reject junction/symlink escapes. External Content Center/JC/SJD roots are protected; JC/SJD filename prefixes alone do not disqualify eligible files *inside* the verified old-project root. Read-only, unknown Vault checkout ownership and dirty/open documents fail closed.
- **Pure planning**: input existing string, filename stem where applicable, target `PJ#####`, approved property mapping; output typed proposed changes or explicit unchanged/identity-unverified. Change only leading `PJ#####-` token, retain full suffix; never create a missing property or change a revision. Approved model mapping: Design Tracking Properties / Part Number; Inventor User Defined Properties / SPECIFICATION. Additional populated fields require a separately reviewed allowlist. Drawing mapping currently restricted to existing custom DRAWING_NUMBER with matching filename/field old project identity; validate mapping against disposable Inventor drawing fixtures before APPLY.
- **Mutation and persisted verification**: input approved immutable plan + file precondition fingerprint + explicit APPLY authorization; output per-file saved/readback/failed status. APPLY is unavailable until Vault checkout authority, dirty-state handling, write failure recovery and independent close/reopen persisted readback are proven. Never change source files; target only explicitly authorized disposable project copies. COM hang requires external watchdog/abort strategy; a Try/Catch is not a timeout.
- **Logging**: input structured event; output append-only run manifest, per-file old/new values, skip/fail reason, engine version, source SHA, precondition and post-save evidence. Logging failures must not silently permit APPLY.
- **UI**: input active GA and prompt response; output normalized project target and preview/explicit APPLY request. Default dry-run; no business logic.

## Evidence and regression gates

1. Confirm both wrappers reference canonical planners; reject duplicate local `PlanDrawingNumber`, `ReplaceLeadingProject` or `QueuePrefix` implementations.
2. Execute source-contract tests and offline behaviour tests against the **actual canonical implementation** (not a Python mirror alone); record commands, test counts and source SHA.
3. Cover invalid prefixes, unchanged values, malformed existing prefix, suffix preservation, drawing filename/field mismatch, nested assembly references, duplicates/cycles, sibling-project paths, external CC/JC/SJD roots, eligible JC/SJD filenames inside old root, read-only/Vault/dirty documents, missing fields, logging failure and partial save/readback failure.
4. Require disposable Inventor 2025/Vault fixture tests before enabling APPLY; capture persisted readback after closing and reopening files. No Inventor runtime qualification is implied by static checks.
5. Only after all property-test gates pass, build thin Clean Sweeper integration adapter calling the identical canonical implementation. Keep Existing Target Repair separate.

## Verified source-level blocker (2026-11-15)

The current standalone `scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb` contains its own `PlanDrawingNumber`, `ReplaceLeadingProject`, `QueuePrefix`, `EligibilityReason` and `WriteLine`. It does not invoke `BEEXCITED_PropertyRefreshPure.PlanExistingModelProperty` or `PlanExistingDrawingProperty`. Its APPLY path is blocked, but contains unqualified in-memory post-save readback. This contract is a development gate, not a working integration or tested candidate.
