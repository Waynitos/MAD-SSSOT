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

## Flight Success Metrics — capture wins and learning, not just failures (2026-11-24)

**Scope:** All BEEXCITED flights, pilots and MAD runs. Use the existing run/issue/Black Box record; do not create a second administrative platform. Record a small *before → after* evidence row on each meaningful flight, even if it succeeds first time. A flight can yield a **success pattern** for others to reuse, just as failure yields a mitigation.

| Measure | Exact capture rule | Why it matters |
|---|---|---|
| User outcome | Defined acceptance scenario and **PASS / FAIL / BLOCKED / UNVERIFIED** on the intended environment, with a source/test receipt | Prevents green tests masquerading as product delivery |
| Time to usable result | Timestamp of accepted request → timestamp of first verified user result; minutes/hours, or **not measured** | Shows faster delivery rather than activity volume |
| MU interventions | Count of times MU had to repeat, chase, manually dispatch or troubleshoot; exclude intentional strategic approvals | Measures whether we are bearing burdens |
| Reuse versus rework | Existing product/component reused; bespoke components built; unnecessary iterations avoided or experienced | Tests Just Use Pencil |
| Verification quality | Static test / isolated automated test / integrated browser / **live end-user acceptance**, recorded separately | Makes evidence comparable |
| Repeat failure avoided | Relevant prior Black Box ID, countermeasure applied, evidence of PASS / FAIL / UNVERIFIED | Tests knowledge transfer and prevention |
| Practical gain | One grounded measure appropriate to flight (successful requests, manual steps avoided, processing time, error rate, cost or satisfaction), with baseline and units | Demonstrates positive value and improvement |

**Lightweight flight record:** `flight_id | objective | before/baseline | change/reused solution | target environment | acceptance result + evidence | start/end timestamps | MU interventions | test depth | applicable Black Box ID + application result | practical gain | next improvement`. Unknown metrics must be `not measured` or `unverified`, never invented; don't infer a cost or speed improvement from anecdote.

**Promotion loop:** After a verified success, extract the reusable recipe and link it from the living knowledge index. After a failure, record a corrective rule and test it on the next eligible flight. DA/SSA challenge unsupported success claims. SA periodically compares *actual* flights: acceptance ratio (verified PASS / flights with acceptance attempted), median time to result, MU chases per flight, reuse rate, and repeat-stall incidence; publish no percentage or trend until comparable sample data exists. Do not count GitHub commits, agent messages or documents as a success factor in themselves.

**Initial Penelope baseline (observed):** Existing production idea submission and historical report retrieval demonstrated in earlier pilot evidence; genuine AI conversation on production **UNVERIFIED / user-reported unavailable**; user follow-up required **YES**; time-to-usable-conversation **not achieved**; preflight Black Box mitigation recorded but runtime impact **unverified**. On the next operational trial, compare these same measures against the live result rather than starting fresh.

## Horizon Watch
*(Upcoming methods, tools, or competing approaches)*

- Track new MAD papers and agent frameworks (LangGraph preferred over AutoGen for production)
