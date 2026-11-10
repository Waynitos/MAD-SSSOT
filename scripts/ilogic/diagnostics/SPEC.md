# iLogic Diagnostic Library — Proposed Specification
_Last updated: 2026-11-11_
**Status: PROPOSED** — architecture and workflow proposal, not an implemented diagnostic engine.

## Purpose
Reusable, independent, predominantly read-only Inventor/iLogic diagnostic rules to establish observed object state, API capability, and manual-command effects before writing automation. Serves iLogic ASSASSIN, CLEAN SWEEPER, and other BEEXCITED projects; does not automatically integrate into them.

## Entry point
Engineer selects a diagnostic from a future Front Desk Code Audit / Diagnostics entry point, or runs an approved standalone `.iLogicVb` rule in Autodesk Inventor. Portal integration is not yet implemented.

## Step-by-step flow
1. Define manual workflow, Inventor version, document type, exact selection/operation, and question to answer.
2. Search MAD-SSSOT for an existing diagnostic and known API constraints before writing a new one.
3. If API behaviour is uncertain, design a minimal diagnostic: identify object(s), capture before-state, guide operator to perform the manual action, capture after-state, and calculate differences. For command events, record only exposed Inventor events/identifiers; do not imply access to private internal functions.
4. Confirm safety: read-only default, no automatic Save, Replace, Update, checkout, or mutation. A manual operation may change the document; require an explicit disposable-copy/safe-environment warning and consent when relevant.
5. Run static checks against `scripts/ilogic/ILOGIC_EDIT_PROTOCOL.md`; distinguish static review from actual Inventor compile/runtime evidence.
6. Produce a structured report: source/version, object identities, state diffs, relevant API candidates, unsupported/unavailable properties, exceptions, interpretation and limitations.
7. Record evidence and regression results. Promote findings from PROPOSED → INVESTIGATING → IMPLEMENTED → TESTED → VERIFIED only with matching evidence.
8. Evaluate separate handoff to project code with explicit approval and regression review; never silently merge diagnostics into production rules.

## Proposed library structure
- `scripts/ilogic/diagnostics/` — one canonical file per diagnostic, complete `.iLogicVb` files only.
- `scripts/ilogic/diagnostics/SPEC.md` — this authoritative proposal.
- `knowledge/` — reusable API observations, failures and fixes.
- `runs/` — test evidence and MAD review records as appropriate.

## Key variable notes
| Variable | Meaning | Set where |
|---|---|---|
| `sourceDocument` | Current drawing/part/assembly identity | Start of diagnostic |
| `targetObjects` | Explicitly selected object(s) | Selection stage |
| `beforeState` | Snapshot of exposed properties/geometry | Before manual action |
| `afterState` | Snapshot after manual action | After operator confirmation |
| `diffReport` | Changes, exceptions and interpretation | Comparison stage |
| `status` | Evidence-based lifecycle label | Review/report stage |

Names are conceptual; not a commitment to a shared code framework.

## Constraints
- Autodesk Inventor's public API does not expose every internal function invoked by a manual UI operation. Command/event observation and state comparisons are evidence, not guaranteed traces of internal calls.
- Diagnostics must not claim a particular API method was called merely because an equivalent manual effect was observed.
- Respect Vault checkout/issued drawing constraints. Use disposable copies for any manual action that changes document state.
- Preserve iLogic compatibility: `Sub Main` first executable; no blocked System.Drawing Font/color APIs; no truncated files.
- Diagnostic execution and compilation require actual Inventor access; none is asserted here.
- Avoid mandatory instrumentation for trivial, already-understood API operations; use when uncertainty or risk justifies it.

## Commit history (key milestones)
| Commit | What |
|---|---|
| Initial proposal | Establish diagnostic-first workflow and dedicated library specification (2026-11-11) |
