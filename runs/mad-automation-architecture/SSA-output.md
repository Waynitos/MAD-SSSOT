# SSA Synthesis: Claude Projects as MAD Automation Layer

**Date:** October 2026  
**Run type:** General MAD  
**Subject:** Can Claude Projects serve as the automation layer for the MAD multi-agent workflow — with phone-accessible, zero-friction UX?

---

## Recommendation: CONDITIONAL GO

Proceed with Claude Projects as Phase 1 — with three explicit conditions:

1. **Verify fork output capture end-to-end** — ✅ CONFIRMED. This run is the proof. AA→DA→SSA completed with zero manual relay steps.
2. **Accept the isolation tradeoff explicitly** — forked MAD is not identical to manual three-session MAD. Document as a known design choice, not a claim of equivalence.
3. **Solve the notification gap before relying on "walk away"** — iPhone push notification via Safari browser tab is not reliable. Mitigation: deliver a short 3–5 bullet summary when SSA completes; link to full artifact for desktop reading.

---

## What Is Confirmed True

- **The fork chain works.** This run — AA spawned, DA spawned with AA output embedded, SSA synthesising — is live evidence. Zero manual relay. Core requirement met.
- **Zero deployment friction is real.** No server, no API keys, no CORS, no uptime management.
- **Phone access works at the trigger level.** Opening MAD PROJECT on an iPhone and typing "Run MAD on X" works.
- **The prompt library and data model port to Phase 2.** Topic configs, checklist structure, runs/ folder convention are reusable regardless of what orchestration layer follows.
- **GitHub integration works in an active session.** Reading topic configs, committing outputs — confirmed.

---

## What Is Likely True But Unverified

- Background forks continue if the browser tab closes (almost certainly true — not explicitly confirmed)
- Rate limits allow 3–5 parallel MAD runs on Pro/Team plan
- Scheduled tasks can load project context (plausible, untested — do not rely on until confirmed)

---

## What Is Genuinely Uncertain

- Concurrent fork limits (no public documentation — test empirically)
- Session persistence across phone lock
- GitHub credentials in fresh/scheduled sessions

---

## The Isolation Question — Honest Answer

Forked MAD is not identical to manual three-session MAD. The DA fork receives a prompt authored by a parent that has already processed the AA output — one layer of anchoring exists.

**However:** this is not a fatal flaw. The DA fork's instructions explicitly direct it to attack the AA. In practice, this run's DA output demonstrated genuine critical independence — it found real weaknesses the AA overclaimed.

**Decision:** Forked MAD is good enough for Phase 1. A weaker form of isolation that actually gets used beats a purer form that doesn't. Document the tradeoff in FRAMEWORK.md and revisit if output quality degrades.

---

## The Phone Experience — Honest Answer

**Works:** Triggering a run. Reading a summary reply. Opening an artifact link.  
**Doesn't work:** Push notification when results arrive. Reading full structured SSA reports comfortably on phone (tables, risk registers need desktop).  
**The fix:** Short summary reply (3–5 bullets) when SSA completes + artifact link. Phone gets the verdict; desktop gets the detail.

---

## The App Transition — Honest Answer

Phase 1 (Claude Projects) is a **prompt laboratory and UX research tool**.  
Phase 2 (app) is a **production system built on the lessons of Phase 1**.

What carries over: prompt library, topic configs, data model, UX patterns.  
What gets rewritten: everything currently handled by the Agent tool → async API calls, job queue, database, notification service.

They share DNA, not code. That is a good outcome.

---

## Unresolved Risks Register

| Risk | Severity | Status |
|------|----------|--------|
| Fork output capture silent failure | **Critical** | ✅ Tested — this run confirmed working |
| No iPhone push notification | **Significant** | Known gap — mitigate with short summary reply |
| GitHub credentials in future sessions | **Significant** | Monitor — re-auth if needed |
| Concurrent fork limits unknown | **Significant** | Test before building parallel-run UX |
| Vendor lock-in / API changes | **Significant** | Accept for Phase 1, pin model versions in Phase 2 |
| Isolation weaker than manual MAD | **Minor** | Accepted tradeoff — document in FRAMEWORK.md |
| Scheduled tasks cold-start | **Minor** | Do not rely on scheduled runs until tested |

---

## Next Steps — In Order

1. ✅ **This run confirmed fork chain works.** Record it.
2. **Build the MAD orchestrator skill** — SKILL.md that handles "Run MAD on [subject] using [topic type]"
3. **Test phone UX end-to-end** — trigger from iPhone, close tab, check what's waiting
4. **Test parallel runs** — two simultaneous topics, observe fork behaviour
5. **Document isolation tradeoff in FRAMEWORK.md**
6. **Do not build the app yet** — run 5–10 real MAD cycles through the orchestrator skill first

---

*This SSA output was itself produced by a fully automated MAD cycle — AA → DA → SSA — with zero manual relay steps, run entirely within Claude Projects. The method validated itself.*
