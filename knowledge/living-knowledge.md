# Living Knowledge Base

## Failure Modes
*(Add new failure modes discovered during MAD runs here)*

- Incomplete first-pass information that requires user discovery
- Bot-blocking or data-access restrictions (e.g. travel sites)
- Hidden costs or required accessories not disclosed early
- Mode exclusivity (cannot run two features simultaneously)

- **BBX-2026-11-24-01 — Flight stalls despite green internal progress:** Penelope front-desk development repeatedly produced new HTML pilots, PR/test reports and new candidate architecture while the live portal still could not greet, converse or retain a user dialogue. User was forced to chase the issue. Full evidence/transfer lesson: [Penelope Black Box](failure-mode-penelope-delivery-stall-2026-11-24.md). **Countermeasure for every next flight:** before any custom build, review existing implementations; define one user-visible acceptance; do a working end-to-end test on the actual target; treat blocked deployment or absent tool access as an immediate exception, not green status. **This entry is recorded/propagated as instruction, not yet verified as autonomous runtime enforcement.**

## Protocol Updates
*(Record improvements recommended by SA or validated in runs)*

- SSA must always close with next-best alternative recommendation + horizon analysis (added 2026-10-18)

## Horizon Watch
*(Upcoming methods, tools, or competing approaches)*

- Track new MAD papers and agent frameworks (LangGraph preferred over AutoGen for production)
