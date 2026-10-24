# DA Output — MAD Routing Strategy
**Agent:** DA (Devil's Advocate)
**Date:** 2026-10-24
**Position:** Against broad MAD auto-triggering — precision routing is better

---

## The Classifier Will Betray You

The AA position assumes a classifier can reliably identify "debate-worthy" queries. It cannot. Natural language intent is ambiguous by design — "should I use Python or PowerShell for this?" looks like a decision query but is often a rhetorical warmup before "just write it in PowerShell." A classifier firing MAD on that query wastes two agent runs and produces a verdict the user never needed.

False positives are annoying. False negatives are invisible. The worst outcome isn't MAD triggering unnecessarily — it's MAD silently *not* triggering on the decision that actually mattered, because it looked like a factual lookup. A classifier gives the illusion of coverage while the real decisions slip through the gaps.

## Alert Fatigue Is Real and Fast

MAD is a heavyweight process — AA, DA, SSA, commit to GitHub, produce a verdict table. That's not a background tick; it's a deliberate interruption of the workflow. Run it on 30% of queries and Waynito will learn to scroll past the output within two weeks. The value of a MAD verdict is that it *means something* when it appears. Dilute the signal and you've broken the instrument.

This is the same failure mode as overzealous FTCA alerts — if everything is flagged, nothing is. The AA position would do to MAD exactly what it's trying to prevent FTCAgent from doing.

## FTCA's Threshold Approach Is Actually Correct

The current system — FTCA flags a topic after 3+ revisits and suggests MAD — is not a stopgap. It is the right mechanism, for one key reason: **revisits are evidence of genuine uncertainty**. If Waynito has circled back to the same question three times, that's a real signal that the decision is contested and unresolved. A classifier guessing at intent from a single query has no such evidence.

The FTCA threshold approach should be *tightened*, not abandoned in favour of broad auto-routing. Tighter means: reduce from 3 revisits to 2 for high-stakes domain tags (ARCHITECTURE, TOOLING, STRATEGY), and add a second trigger — any query explicitly framed as a comparison ("X vs Y", "should I use X or Y") routes to a lightweight MAD-lite (AA + DA only, no SSA commit) before escalating to full MAD if the user asks for synthesis.

## The Real Problem Is Query Framing, Not Routing

The gap isn't that the system fails to detect debate-worthy queries. It's that Waynito doesn't always know *when* to reach for MAD. The fix is education, not automation. PLU should include a one-line cue in every project's onboarding:

> *When you're weighing two approaches or making a decision you'll live with for a while — prefix your query with `?MAD` to run a full debate.*

This puts routing intent back with the human, where it belongs. A `?MAD` trigger word costs nothing to implement, generates zero false positives, and trains the right habit: pausing before a decision and consciously choosing deliberate analysis.

## Counter-Proposal: Precision Routing, Not Broad Routing

| Trigger | Action |
|---|---|
| `?MAD` prefix on any query | Full AA → DA → SSA, commit to GitHub |
| Query contains "X vs Y" or "should I use" | Offer MAD-lite in one line: "This looks like a decision — run MAD on it? (`?MAD`)" |
| FTCA: 2+ revisits on same topic (ARCHITECTURE/TOOLING/STRATEGY) | Auto-suggest MAD, don't auto-run it |
| FTCA: 3+ revisits any topic | Auto-run MAD-lite, surface to user |

Precision beats coverage. A MAD that runs when it should — and stays silent when it shouldn't — is worth ten classifiers guessing at intent.
