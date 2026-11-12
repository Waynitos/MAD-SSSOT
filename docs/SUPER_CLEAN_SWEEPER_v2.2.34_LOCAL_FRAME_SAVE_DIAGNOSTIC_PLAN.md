# Frame Generator Local Save Diagnostic — isolated v2.2.34 experiment

## Objective
Reproduce the user's lower-level rerun symptom on a **small disposable Inventor 2025 Frame Generator subassembly**: component replacement succeeds, but saving subsequently prompts about the frame skeleton, resembling a checked-in-file save dialog even when the skeleton is not checked in.

## Scope and isolation
- Separate test harness; no integration into SUPER CLEAN SWEEPER's production Copy Planner/Executor.
- Start with a local workspace containing a single frame .iam, driving master sketch, reference skeleton, and 2–4 generated members.
- No Vault checkout/check-in, file rename, component replace, SaveAs, forced refresh or save in baseline capture.
- Do not automatically dismiss Inventor dialogs or suppress save warnings.
- Use a disposable copy and a baseline archive before any optional mutation phase.

## Test phases
**Phase 0 — Read-only discovery:** record Inventor version, active document, active project (.ipj), each reachable document's full path, document type, dirty state, read-only attribute, reference descriptors, parent-child edges, missing references, skeleton candidates, and whether files reside outside the test root. Record elapsed milliseconds per stage (v2.2.33 profiler convention).

**Phase 1 — Explicit update experiment:** user confirms operation and selects a disposable frame. Snapshot before; invoke only a verified supported update mechanism in the correct document context; snapshot after; log exceptions and which documents became dirty. Verify `AFG_Refresh` availability separately; do not assume it exists.

**Phase 2 — Explicit save experiment:** user confirms and selects exactly which document to save; preflight read-only/permissions, dirty state, references, and Vault status if independently available. Abort on unknown ownership, missing or external dependencies. Capture save API outcome, exceptions, changed file timestamps/hashes, and dirty state. Do not assume save order.

**Phase 3 — Comparison:** compare initial and final dependency graphs and dirty flags; record whether the skeleton requires parent assembly context. Ask user to capture screenshots and exact wording of any native Inventor/Vault dialog, which iLogic may not expose.

## Log schema
run_id, timestamp, Inventor version, project path, test root, phase, duration_ms, document full path/type, parent path, reference descriptor, skeleton classification confidence, dirty_before/after, read_only, vault_state (unknown unless verified), update/save operation attempted, API exception HRESULT/message, native_dialog_observed (manual), native_dialog_text (manual), result, blockers.

## Acceptance criteria
- Can reproduce or falsify the skeleton save prompt on a minimal frame.
- Can attribute dirty-state propagation to a specific operation.
- No unintended modifications during Phase 0.
- No mutation without explicit per-phase approval and verified safe test copy.
- Failed/unknown preflight blocks save rather than guessing.
- Report contains enough evidence to choose whether skeleton-first copy/relink and coordinated frame save are appropriate.

## Follow-on
After the read-only baseline, implement a **separate local diagnostic iLogic rule**, then evaluate controlled update/save on disposable copies. Do not claim Inventor testing until user runs it and supplies logs/screenshots.
