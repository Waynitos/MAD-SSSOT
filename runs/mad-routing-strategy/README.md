# MAD Run: MAD Routing Strategy

**Topic:** When should the MAD cycle auto-trigger vs require manual invocation?
**Date:** 2026-10-24
**Project:** FTCAgent (FTCA)
**Status:** ✓ Complete

---

## SSA One-Line Verdict

> Build the narrow high-stakes detector for Mini-MAD and add `?MAD` shorthand — don't build the broad classifier, don't touch FTCA's threshold.

## Outputs

| File | Agent | Summary |
|---|---|---|
| AA-output.md | Advocate | Case for broad auto-triggering via PLU classifier |
| DA-output.md | Devil's Advocate | Case against — alert fatigue, false positives, async flaws |
| SSA-output.md | Synthesizer | Three-layer model: `?MAD` + Mini-MAD + FTCA unchanged |

## Key Decisions

| Decision | Rationale |
|---|---|
| Add `?MAD` shorthand to PLU | Zero friction, zero false positives — both sides accept |
| Mini-MAD for high-stakes patterns | Resolves overhead objection; inline, no agents |
| Narrow 5-pattern classifier only | Avoids alert fatigue; high-stakes signals only |
| FTCA 3-revisit threshold unchanged | DA's strongest point — empirical signal beats syntax |
| No broad keyword classifier | DA won this — structural false positive problem |
| No async MAD | DA won this — window closes before output is useful |
