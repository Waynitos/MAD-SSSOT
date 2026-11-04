# MAD Run: Super Clean Sweeper Architecture Audit
*Date: 2026-11-04*
*Rule under review: `scripts/ilogic/SUPER_CLEAN_SWEEPER.iLogicVb` v1.0.0*

## Context

SUPER_CLEAN_SWEEPER is a new, clean-room iLogic rule implementing Copy Design (Mode 6) with a provenance architecture. It was written to replace the equivalent mode in the monolithic TRAVERSE_CLEAN_SWEEPER rule, introducing:

- `SaveAs(newPath, True)` instead of `File.Copy` — to generate fresh GUIDs
- Five CS_ iProperties written to every new file at save time (audit trail)
- `CS_ModelRefs` on drawings for autonomous relink
- A provenance skip guard for safe re-entrant runs
- Three-phase processing: Walk → SaveAs+Provenance → Reference Rewrite

## MAD Outputs

| File | Role |
|------|------|
| `AA-output.md` | Advocate — strongest case FOR the architecture |
| `DA-output.md` | Devil's Advocate — strongest case AGAINST |
| `SSA-output.md` | Synthesiser verdict with prioritised action items |

## SSA Verdict (summary)

**Architecture is sound. Ship v1.0.0 for testing.**

Three items require attention before production use:

| ID | Issue | Priority |
|----|-------|----------|
| ASSUMPTION-1 | SaveAs GUID freshness not yet verified with INVENTOR_EVENT_CAPTURE | P0 — verify on Day 1 |
| BUG-1 | WalkTree leaks open documents (memory accumulation on large trees) | P1 — fix in v1.1 |
| BUG-2 | Phase 3 does not strip DART SHUT state tag from FileDescriptor paths | P1 — fix in v1.1 |

Two P2 logging improvements and one accepted P3 risk are documented in `SSA-output.md`.

## Related

- Rule commit: `8575a6e` — `ilogic: add SUPER_CLEAN_SWEEPER v1.0.0 — clean Copy Design rule with provenance architecture`
- Project doc: `claude/CLEAN_SWEEPER_ROADMAP.md`
- Protocol: `claude/ILOGIC_EDIT_PROTOCOL.md`
