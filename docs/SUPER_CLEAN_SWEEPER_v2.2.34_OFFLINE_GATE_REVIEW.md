# v2.2.34 offline preview gate — source review (2026-11-11)

Commit: 5d6ed575a94e21116357c00f357d60f8e4dc13f3. Scope: `experiments/sweeper-v2.2.34/repair_preview_gate.py`.

## Static inspection
- Standalone Python CLI consumes a JSON inventory; prints a JSON preview. No file rename, save, Inventor API, Vault API, or reference update calls. Output is stdout only.
- Up to five case-insensitive basename substitutions; extensions and directory components remain unchanged.
- Flags incomplete discovery, reverse-reference coverage, Frame Generator verification, Vault clearance and profiling; blocks unresolved/unknown ownership/writability, missing/out-of-root sources, unsupported extensions, duplicate sources, existing destinations, duplicate targets and invalid names.
- Always returns `approved_for_mutation: false`; there is intentionally no mutation path.
- Input example: `{"target_root":"C:\\\\test","substitutions":[["--","-"]],"files":[],"discovery_complete":false}`. Run: `python repair_preview_gate.py inventory.json`.
- No runtime execution or unit tests were performed in this review. This is a manual source-level inspection only.

## DA: important limitations
1. This is an **offline experiment**, not integrated with the iLogic source. Its input claims (including `*_verified`) are not independently authenticated; a caller can set flags true. Never treat the flags as evidence of safety.
2. `os.path` follows the host platform. For Windows Inventor paths, run on Windows; POSIX path semantics are not equivalent. Drive mismatches can raise `ValueError` rather than returning a structured blocker.
3. It does not discover dependencies, reverse references, Frame Generator skeleton relationships, drawings or IPNs. Those must be supplied by a separate complete inventory stage.
4. Existing destination checks are not transactional, and filesystem permissions alone cannot prove Vault checkout/ownership.
5. No rename graph ordering, backup, rollback, Inventor-supported reference repair, reopened-document verification, or integration with v2.2.33 profiler checkpoints.
6. Case-only renames and Windows reserved device basenames require more rigorous handling before any real mutation. Input schema and path escaping require validation/hardening.
7. Even a blocker-free preview is **not** permission to rename. `approved_for_mutation` is always false.

## SSA verdict
Useful isolated preview experiment, **not a complete v2.2.34 candidate**. No production/main or v2.2.33 profiler source was changed. Inventor compilation, execution, Vault and Frame Generator safety remain untested. Next gate: trustworthy complete dependency discovery, authenticated preflight, then an Inventor-aware transactional repair implementation and regression checks.
