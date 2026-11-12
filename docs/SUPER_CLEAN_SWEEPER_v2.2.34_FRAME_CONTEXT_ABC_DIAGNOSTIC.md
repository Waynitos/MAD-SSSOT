# v2.2.34 Frame Generator — assembly-context A/B/C diagnostics

## User observation and hypothesis
Some SUPER CLEAN SWEEPER runs succeed while others fail. User suspects direct operations on a lower-level Frame Generator subassembly may save correctly, while performing equivalent work from a higher-level GA can provoke skeleton save-context dialogs. **Unverified hypothesis; test rather than assume.**

## Minimal read-only SQLite diagnostic prototype
Capture identical evidence from three independently restored/disposable copies of the same frame tree:
- **A — frame context:** open frame .iam directly; record initial graph, dirty flags, document identities, references.
- **B — immediate parent:** open containing subassembly and record same data.
- **C — GA context:** open top-level GA and record same data.

For each test, separate **observation-only** run from an explicitly authorised **controlled update/save** run. Do not automatically update/save during initial diagnostic capture. Use equivalent operation sequence, baseline file contents and active project, with run order and environmental conditions recorded.

## SQLite observations
Store run_id, test_case, baseline_fingerprint, Inventor version, .ipj, Vault status/provenance, active document and occurrence path, document identities, paths, reference edges, skeleton/member classification, dirty/read-only flags, update/save operation, timings, API exceptions and manually recorded native dialog text. Preserve before/after snapshots and all parent-chain paths. Unknown data must remain unknown.

## Controls for intermittent failures
Repeat each case at least three times from an unchanged baseline. Record cold/warm session, open document count, active Model State, update status, checkout state, local vs Vault workspace, and file timestamps/fingerprints. Compare successful and failed runs, not just frame vs GA context.

## Expected outputs
1. Difference report showing whether document context changes the reference graph, dirty propagation, update or save behaviour.
2. Minimal reproduction and exact prompt text/screenshots.
3. Evidence-backed decision whether coordinated Frame Generator save groups or a different API approach is warranted.

No automatic mutation or production/main changes. The SQLite DB is a diagnostic evidence store, not authority for live Inventor/Vault references.
