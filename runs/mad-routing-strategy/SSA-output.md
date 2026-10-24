# SSA Output — MAD Routing Strategy: Verdict + Implementation

*MAD Run: mad-routing-strategy | Role: Synthesizer | Date: 2026-10-24*

---

## Verdict Table

| Claim | AA | DA | SSA Verdict |
|---|---|---|---|
| Decisions don't announce themselves | ✓ Strong | ✗ Disputed — user knows | **Partial AA win** — some do, most don't |
| Keyword classifier is adequate | ✓ "80% is enough" | ✗ False positive rate is structural | **DA wins** — keyword router alone is insufficient |
| Alert fatigue is a real risk | Acknowledged but dismissed | ✓ Strong evidence pattern | **DA wins** — this is the decisive objection |
| FTCA 3-revisit threshold is correct | Too slow | ✓ Evidence-based | **DA wins on threshold, AA wins on gap it leaves** |
| Async MAD is viable | ✓ Proposed | ✗ Window closes before output arrives | **DA wins** — async creates orphaned outputs |
| `?MAD` shorthand is useful | Not raised | ✓ Proposed | **Win-win — both would accept this** |
| Mini-MAD (lightweight inline) is viable | ✓ Proposed | Not challenged | **Win-win — not contested** |

---

## What DA Got Right

The alert fatigue argument is decisive and the AA never fully rebuts it. A classifier that fires on false positives trains the user to ignore it. Once ignored, the router is worse than nothing — it has habituated Waynito to dismiss MAD prompts, including legitimate ones. This is not a theoretical risk; it is the documented failure mode of every notification system that over-fires.

DA is also right that a keyword classifier is structurally inadequate. "Should I use X or Y" catches architecture decisions AND trivial implementation choices indistinguishably. The 80% coverage claim ignores that the 20% false positive rate fires *more often in practice* because trivial questions outnumber architectural ones by volume.

FTCA's empirical threshold — wait for 3 revisits — is genuinely the right signal for "this decision is contested." First-pass questions don't carry that signal.

## What AA Got Right

The gap is real. Decisions made once, quickly, without adversarial scrutiny *do* generate downstream rework. The cost-of-not-MAD argument holds — not universally, but for a specific class of high-stakes, hard-to-reverse decisions (data architecture, file naming conventions, tool stack choices). These are the ones where a single good MAD run at session 1 would have saved hours later.

AA is also right that Mini-MAD (abbreviated inline AA/DA/SSA without full agent spawning or GitHub commits) is a viable middle path that DA didn't challenge. A 90-second inline debate on a high-stakes question is not the same overhead as a full MAD run.

The `?MAD` shorthand proposal (from DA's conclusion) is the cleanest manual trigger mechanism and the AA would accept it.

## Synthesis: The Three-Layer Model

Neither "always auto-trigger" nor "only trigger manually after 3 revisits" is the right answer. The correct architecture is three layers:

### Layer 1 — Instant: `?MAD` shorthand
Any query suffixed with `?MAD` runs the full cycle immediately. Zero classifier, zero false positives, zero friction for the cases Waynito consciously flags. Add to PLU now — one line.

### Layer 2 — Inline: High-Stakes Pattern Detection (Narrow Scope)
Instead of a broad keyword classifier, PLU watches for a *short, high-precision list* of patterns that reliably indicate hard-to-reverse decisions:
- Migration or platform switch ("move from X to Y", "migrate", "replace X with")
- Naming or schema decisions ("what should I name", "how should I structure", "schema")
- Stack lock-in ("commit to", "go all-in on", "standardise on")

When detected on first occurrence: offer Mini-MAD inline (not full MAD). Mini-MAD = AA paragraph + DA paragraph + one-line verdict, all in the same response. No agents, no GitHub commit, no waiting. User can escalate to full MAD or dismiss.

This is a 5-pattern list, not 15. High precision, low false positive rate. Doesn't fire on "should I use a for loop."

### Layer 3 — Deferred: FTCA Pattern Detection (unchanged)
Keep the 3-revisit threshold as-is. This catches decisions that *seemed* simple on first pass but proved contested. Full MAD with GitHub output. No change needed here — DA correctly identified this as the right signal for full MAD.

---

## Win-Wins

1. **`?MAD` shorthand** — both sides accept it, implement immediately in PLU
2. **Mini-MAD** — AA proposed it, DA didn't challenge it; it resolves the overhead objection while giving more scrutiny than a single-take answer
3. **Narrow high-stakes classifier** — gives AA the proactive detection it wants without DA's false-positive problem
4. **FTCA threshold unchanged** — DA's strongest point; keep it for full MAD escalation

---

## Implementation Directives

**PLU update (immediate):**
```
## MAD ROUTING — THREE LAYERS
Layer 1 — Manual: any query ending ?MAD → run full MAD cycle immediately
Layer 2 — Inline Mini-MAD: fire on high-stakes patterns (migration, naming/schema, stack lock-in, "commit to X")
  → Deliver AA + DA + verdict inline in same response. No agents, no commit.
  → Offer "escalate to full MAD?" at end.
Layer 3 — FTCA deferred: 3+ revisits on same topic → suggest full MAD run (unchanged)
```

**Not recommended:** broad keyword classifier, async MAD, full auto-trigger on first occurrence.

---

## SSA One-Line Verdict

> Build the narrow high-stakes detector for Mini-MAD and add `?MAD` shorthand — don't build the broad classifier, don't touch FTCA's threshold.
