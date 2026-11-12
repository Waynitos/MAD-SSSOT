# v2.2.34 — bottom-up, same-frame hierarchical diagnostic

User refinement: **start at the lowest-level Frame Generator assembly and move upward through each containing assembly to GA, testing the exact same frame and skeleton**. The objective is to find the first parent context where a previously successful operation/save fails.

## Method
1. Select one small frame with skeleton and generated members. Identify its unique occurrence path through immediate parent(s) to GA/GA drawing.
2. Capture a frozen baseline and restore that identical baseline before each test. Do not use a previously saved/mutated run as the next test's starting point.
3. At depth 0, open the frame directly; record document identities, reference graph, dirty flags, paths, Vault/read-only status and timings. Only after separate user approval perform an update/save experiment on a disposable copy.
4. At depth 1, open its immediate parent and repeat equivalent operations against **the same underlying frame**; restore baseline first.
5. Continue one ancestor at a time until GA; optionally test drawing context last. Include every intermediate ancestor rather than jumping directly from frame to GA.
6. Compare each level with the preceding successful level, finding the **first divergence** in reference resolution, active context, dirty-state propagation, update result, save prompt or exception.
7. Repeat each level from clean baseline to account for intermittent successes/failures; log cold/warm Inventor session, active project, Model State and open-document set.

## SQLite evidence
Capture run_id, baseline_fingerprint, frame_identity, occurrence_path, parent_depth, active_document, open_document_set, reference_edges, skeleton_identity, dirty_before_after, vault_state_provenance, read_only, operation, API_error, native_dialog_manual_capture, elapsed_ms, success/failure. Preserve immutable snapshots.

## Interpretation
- If depth 0 works and depth 1 fails, inspect immediate parent context, save propagation and dependencies.
- If all assembly depths work but drawing context fails, inspect drawing/GA interactions.
- If failures occur at varying depths, investigate nondeterministic state (Vault, session, update order, dirty documents).
- No assertion that save order is root cause until tests support it.

No writes in baseline diagnostic phase; mutation experiments require disposable copies and explicit per-phase confirmation. Do not change production/main.
