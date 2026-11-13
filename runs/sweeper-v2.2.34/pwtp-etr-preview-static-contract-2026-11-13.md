# PWTP-ETR-01 — Existing Target Repair preview gate and static test contract

**Status:** INVESTIGATING / design-and-source gate only. Not a complete v2.2.34 candidate; not compiled or executed in Inventor.

## Inspected actual source
- Baseline: `diagnostic/sweeper-v2.2.33-profiler`
- Work branch: `feature/sweeper-v2.2.34-existing-target-repair`
- Rule: `scripts/ilogic/TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb` (221,256 characters, header v2.2.32).
- Prior gate inventory: `runs/sweeper-v2.2.34/pwtp-source-gate-inventory-2026-11-12.md`.

## Fail-closed acceptance contract
1. **Entry:** explicit Existing Target Repair mode; target is already copied. Never route it through new-copy Phase 2, which can clear file read-only attributes.
2. **Preview:** no Inventor or filesystem mutations; enumerate assembly occurrence edges AND document descriptor edges, old/new mapping, identity/provenance, intended replacement, collision ownership, external references, drawing/IPN references, FG skeleton/member/master-sketch dependencies and unknown edges. Preview must show unresolved state and stop execution.
3. **Collision and Vault:** every target must be unambiguously owned and writable. Read-only, checked-in, unknown Vault state, missing file, duplicate destination, conflicting fingerprints or missing backup -> BLOCKED. Do not change attributes or bypass checkout.
4. **Transaction:** snapshot and durable journal before mutation, stage disposable backups, recheck fingerprints immediately before changes, dependency-order writes, abort on failure, restore from backups only with explicit recovery authority. Mark incomplete recovery BLOCKED and retain evidence.
5. **Verification:** verify in-memory occurrence paths and file descriptors; close/reopen disposable target to verify persisted references. Frame Generator must retain editable skeleton/member associativity and correct context. A successful Replace or Save2 alone is insufficient.
6. **Profiling BBⁿ-PROF-001:** version/run ID, total duration in popup and log, stage durations, failure elapsed times, reference/operation counts, comparable before/after measurements.
7. **Promotion:** source checks and controlled Inventor 2025 runs on disposable copies. No runtime claims from source inspection.

## Source-level check matrix
| ID | Check | Expected |
| --- | --- | --- |
| S01 | Existing-target mode never invokes new-copy SaveAs or raw File.Copy fallback | PASS required |
| S02 | No `File.SetAttributes` read-only clearing reachable in repair | PASS required |
| S03 | Preview has zero mutation calls and logs deterministic planned operations | PASS required |
| S04 | Collision, read-only, Vault unknown and provenance ambiguity all fail closed | PASS required |
| S05 | FG relationship discovery is API-grounded, not filename-only | PASS required |
| S06 | Journal, backups and recovery state are durable before first write | PASS required |
| S07 | Reopen verification checks persistent paths and FG editability | PASS required |
| S08 | Total/stage/failure timing and version IDs recorded | PASS required |
| S09 | Regression comparison against profiler baseline | PASS required |

**Current result:** S01–S09 NOT RUN on a complete candidate. Existing monolithic rule exhibits unsafe patterns identified in prior inventory; therefore no release readiness claim.

## PWTP experiment sequence
- ETR-01: preview-only assembly/occurrence/descriptor graph with profiling.
- ETR-02: controlled writable/Vault preflight and fingerprint collision matrix.
- ETR-03: journal and recovery on disposable copies, including injected save failures.
- ETR-04: skeleton/member/parent same-frame comparison in Inventor 2025.
- ETR-05: guarded transaction plus reopen verification and profiler regression.

**Next action:** implement ETR-01 executable preview independently of the existing monolithic rule, then statically review and submit for MU Inventor test. No production/main changes.
