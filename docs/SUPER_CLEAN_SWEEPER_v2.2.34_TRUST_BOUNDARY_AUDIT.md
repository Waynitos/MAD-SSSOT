# SUPER CLEAN SWEEPER v2.2.34 — trust-boundary audit

Status: **BLOCKED / PREVIEW-ONLY**. Reviewed against `feature/sweeper-v2.2.34-existing-target-repair` after commit `0db5335d7081934f23daa7c20508e830f3601375`. Baseline: `diagnostic/sweeper-v2.2.33-profiler`.

## Source-level observations

- `repair_preview_gate.py` always returns `approved_for_mutation: false` and has no mutation entry point.
- The gate reads `discovery_complete`, `reverse_references_complete`, `frame_generator_verified`, `vault_clearance_verified`, `profiling_available`, and per-file `references_resolved`, `ownership_verified`, `writable_verified` directly from caller-provided JSON. These are **claims, not independently authenticated evidence**.
- `READ_ONLY_REFERENCE_INVENTORY.iLogicVb` walks forward document descriptors for .iam/.ipt children only. It writes a diagnostic text report, not the certified JSON schema consumed by the gate. It does not prove reverse-reference completeness, drawing/IPN coverage, Frame Generator skeleton ownership, or Vault checkout status.
- Case-insensitive directory scans reduce obvious Windows destination collisions, but the scan and subsequent filesystem state are not atomic. A passing preview must not be used as mutation authorisation after a time gap.
- No complete transactional Inventor reference update, rollback, or reopen-and-verify implementation exists in this feature diff.

## Mandatory next implementation sequence

1. Define a **versioned evidence manifest** produced by Inventor-side discovery: target GA identity, canonical target root, per-document identity and reference edges, discovered drawing/IPN reverse edges, Frame Generator skeleton/member relationships, Vault identity and checkout ownership, discovery errors, timestamp and tool version. Treat missing/unknown evidence as blocking.
2. Separate `preview` from `execute` with distinct explicit user selection. Never infer authorisation from a JSON boolean. Require a fresh Inventor-side preflight at execution time and compare identities, paths, reference edges and file state to the approved preview.
3. Establish a complete reference graph before any rename; enforce a deterministic dependency order and prohibit bare filesystem renames for Inventor-linked files. Include a dedicated Frame Generator regression fixture.
4. Capture restorable backups and an append-only journal **before** first modification; stop on any failed operation. Never claim atomic rollback unless the actual Inventor/Vault lifecycle supports it; otherwise report exact recovery steps.
5. Reopen the copied top GA and all affected drawings/IPNs from disk and verify every reference against the approved graph; independently check Frame Generator relationships. Preserve the v2.2.33 profiler checkpoints and add per-stage timing.
6. Run the committed Python regression suite on the **exact GitHub commit**, then compile and test the iLogic rule in an isolated Inventor/Vault test environment. Offline tests alone cannot establish Inventor safety.

## Release rule

Do not label v2.2.34 complete or notify readiness until the separate repair implementation is committed, source-level tests and static review are documented, and the remaining Inventor execution caveat is explicitly stated. Production/main and the profiler baseline must remain unchanged.
