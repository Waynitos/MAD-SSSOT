# PWTP — v2.2.32 observed successful Frame Generator UI baseline (2026-11-13)

**Status: TESTING; not Inventor-verified.** This is user-reported run evidence, not an automated validation or an Existing Target Repair implementation.

## Observations supplied by designer
- SUPER CLEAN SWEEPER v2.2.32 completion dialog: rename map 4,161 files; Phase 2 SaveAs 416 saved / 0 failed; Phase 3 reference fixes 531 / 0 failed; elapsed 01:13:55.
- An interactive historical *Working Drawing Stamp* iLogic event-triggered dialog interrupted unattended progress until the designer clicked OK. Thus elapsed time includes an unknown operator-wait interval and **cannot be used as an uncontaminated performance benchmark**.
- Browser screenshot of new `PJ00183-3450-6-V0-04.iam` showed renamed member occurrences and `PJ00183-3450-6-V0-04-F_ReferenceCopy:1`. The designer confirmed Frame Generator commands/icons are **not greyed out**.
- No evidence yet of actual Change/Trim operation, save/close/reopen, frame member/skeleton provenance, Vault ownership, or exhaustive persisted-reference verification.

## Implications for v2.2.34 Existing Target Repair
1. Preserve v2.2.32 and its successful copy workflow; Existing Target Repair is a **separate opt-in post-copy path** for already-copied assemblies, not a rewrite of the successful copy pass.
2. Existing Target Repair must **not** infer broken Frame Generator associativity solely from `ReferenceCopy` naming or infer success solely from enabled icons.
3. Do not overwrite or repair a Frame Generator subtree when skeleton/member identity, provenance, reference ownership, Vault status, or rollback is unknown. Block and log the reason.
4. Separate wall-clock from active processing time; record user-wait/event-trigger interruption where observable, and retain total/stage/error timing.
5. Test against disposable copies: inspect exact reference paths and `InternalName` compatibility; run a member edit; save/close/reopen; verify no old-project references, warnings or association loss.
6. Interactive drawing event rules must be disabled in a controlled test configuration or made explicitly batch-aware; do not silently suppress required drawing validation in production.

## Source inspection
- `scripts/ilogic/TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb` remains v2.2.32 (Git blob `a45cc8d0bbc5ff47792f565d02aca6076e651f2b`).
- `scripts/ilogic/experiments/SCS_EXISTING_TARGET_REPAIR_GRAPH_PREVIEW_v0_2_0.iLogicVb` remains **read-only** (Git blob `c1ffafd40096d93a599ad21853dbd1ebb624072c`).
- Neither is a complete Existing Target Repair candidate. No Inventor compile/runtime tests were performed in this run.

## Release gates still open
- Explicit preview-to-commit approval boundary and unambiguous path mapping/provenance.
- Occurrence-specific reference replacement with before/after identity checks and bottom-up persistence.
- Frame Generator skeleton/member associativity verification.
- Vault checkout/lock, read-only, collision, dependency-cycle and target-path safeguards.
- Durable backup/journal, bounded rollback and recovery verification.
- Static source-level tests of all fail-closed paths and performance profiling.
- Disposable-copy Inventor 2025 compilation and execution validation (separate from source-level readiness).
