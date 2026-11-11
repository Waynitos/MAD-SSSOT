# Existing Target Repair — evidence manifest contract (draft v1)

Status: **DESIGN ONLY — NOT A TRUSTED CERTIFICATE OR MUTATION AUTHORISATION**. This document defines the data required before a separate repair executor can be designed. The current Python preview gate does not validate this contract.

## Envelope

```json
{
  "schema": "scs.existing-target-repair.evidence.v1",
  "producer": {"name": "Inventor-side read-only discovery", "version": "UNIMPLEMENTED"},
  "captured_at_utc": "2026-11-12T00:00:00Z",
  "target": {"root": "C:\\CopiedProject", "top_ga": "C:\\CopiedProject\\GA.iam"},
  "documents": [],
  "edges": [],
  "frame_generator": [],
  "vault": {"provider": "UNVERIFIED", "identity": null, "clearance": "unknown"},
  "discovery": {"errors": [], "complete": false},
  "profiler": {"baseline": "v2.2.33", "checkpoints": []}
}
```

**The example above must be rejected**: producer is not authenticated, discovery is incomplete and Vault clearance is unknown. The schema name is a version discriminator, not proof of origin.

## Required document evidence

Each document needs a stable Inventor identity where available, absolute canonical path, file type (.iam/.ipt/.idw/.dwg/.ipn), current file size and modification timestamp, content hash (SHA-256), filesystem reparse/symlink status, read-only state, Vault identity and checkout owner, and discovery error list. Distinguish **existing copied target** from old source: never infer identity from basename alone. Include drawings in the main folder and `Non Std Parts`, and IPNs used by exploded views.

Each reference edge records **parent identity, child identity, reference kind, resolved path, resolution status and discovery API**. Collect forward and reverse references, including drawing model references, IPN presentation links, Frame Generator member-to-skeleton relationships and derived/adaptive links where relevant. An edge is not certified merely because the referenced file exists.

Frame Generator records need frame assembly, skeleton/source sketch, generated member identity, dependency edge, ownership/checkout status and whether any member still points outside the copied target. Missing skeletons or unresolved external references block execution.

## Preflight invariants

1. Reject unsupported schema versions, missing fields, duplicate or ambiguous identities, unresolved edges, discovery errors, unknown Vault status, paths escaping the canonical target, reparse-point escapes and case-insensitive path collisions.
2. Require the copied top GA to exist and its complete reachable dependency graph to be enumerated; record reverse consumers and distinguish deliberate external/library references from accidentally retained old-project references. No automatic substitution of Content Center or library files.
3. Require an **independently established** producer identity and fresh Inventor/Vault readback. Caller-controlled booleans, hashes and timestamps are assertions, not certificates. A JSON manifest alone cannot authorize modification.
4. At execute time, re-enumerate the graph and compare identities, reference edges, Vault state and file fingerprints with the reviewed preview. Any mismatch aborts before mutation.
5. Never rename an Inventor-linked file with an ordinary filesystem move. Use an explicit, separately implemented Inventor-aware repair transaction with journal and restorable backups, followed by disk reopen and verification of GA, drawings, IPNs and Frame Generator links.
6. Preserve v2.2.33 profiling checkpoints and add timing for discovery, preview, preflight, each reference replacement, save, reopen, verification and recovery.

## Execution ordering and recovery

Plan from dependencies outward: verify copied GA and its subassemblies first, repair lower-level subassemblies and Frame Generator dependencies in a graph-aware order, then update the top GA, and relink independent drawing models **last**, after GA success. Include IPNs and drawing consumers in the final verification. Capture before-state and backup evidence before the first write; journal every attempted operation and result. On failure stop and report the precise partially modified set and recovery actions. Do not promise atomic rollback across Inventor and Vault.

## Acceptance gates

- Offline: schema validation, malformed/missing evidence, duplicate identities, Windows case collisions, escaped paths, unresolved references, stale snapshots and deterministic planning tests on the exact commit.
- Static: review that the preview has no CAD/Vault mutation path and execution is separately gated.
- Inventor/Vault: compile, run on disposable copied assemblies with Frame Generator skeletons, drawings and IPNs; verify actual links and rollback behavior. **Not performed**.

No production/main or v2.2.33 profiler changes are authorised by this contract.
