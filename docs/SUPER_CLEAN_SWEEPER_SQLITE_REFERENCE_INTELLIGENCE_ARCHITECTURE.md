# SUPER CLEAN SWEEPER — SQLite reference intelligence architecture proposal

Status: **design proposal only**, not implemented or verified against the existing source. Keep isolated from production/main.

## Purpose
Build a persistent, queryable evidence and planning layer across ordinary Inventor assemblies, Frame Generator skeletons/members, drawings, IPNs and Vault-managed files. Reuse current Indexer / Copy Planner / Executor architecture; SQLite is **not** authoritative over live Inventor or Vault state.

## Identity model
- **File instance:** canonical path, file fingerprint, size, modification time, Inventor project context; do not use path alone as stable identity.
- **Inventor document lineage:** capture documented InternalName and other supported identifiers with provenance and caveats. Do not assume a copy gets a new InternalName.
- **Occurrence:** assembly-specific occurrence identity/path, not conflated with file identity.
- **Reference edge:** from document/occurrence to referenced document, reference type, resolution status, source API, evidence timestamp.
- **Frame Generator metadata:** skeleton/master-sketch/generated-member relations, only where supported and actually observed.
- **Vault identity:** Vault master/file/version IDs and checkout state when authenticated and available; preserve version-specific provenance.
- **Copy mapping:** explicit source instance -> intended target instance, including rename policy and verification state.

## Candidate normalized tables
`scan_runs`, `file_instances`, `document_identities`, `occurrences`, `reference_edges`, `frame_relationships`, `vault_observations`, `copy_mappings`, `repair_operations`, `repair_events`, `file_fingerprints`, `diagnostics`.

Every observation must include scan/run provenance, API source and confidence; preserve immutable historical snapshots rather than overwriting evidence. Index source/target identity and reverse-reference lookups. Schema migrations and referential integrity required.

## Integration phases
1. Inspect existing Indexer, Planner, Executor and profiler code before designing adapters.
2. Build read-only SQLite prototype ingesting existing manifests; compare graph results with current pipeline.
3. Add GUID/metadata and Frame Generator read-only diagnostic data from disposable Inventor 2025 frames.
4. Implement graph diff, stale-edge detection, reverse impact, target collision detection, and incremental scan invalidation.
5. Add guarded repair planning and transaction journal. No execution based solely on cached records.
6. Evaluate performance and correctness against nested PJ00201 subs, drawings, IPNs and Frame Generator skeleton save-context reproduction.

## Guardrails
- Re-read Inventor references and independently verify Vault rights immediately before mutation.
- No undocumented XML/binary metadata modification.
- Database transaction does not make Inventor filesystem operations atomic; require separate operation journal, backup/recovery and post-write readback.
- Record uncertain relationships as uncertain; never manufacture GUID or reference links.
- No claims of implementation or Inventor runtime validation until evidenced.

## Success criteria
For any copied subassembly, answer: original identity and lineage; intended target; all inbound and outbound references; which references remain stale; what changed across scans; what repair operations are safe; and why a skeleton/frame save was blocked.
