# FLIGHT-STRESS-ASSASSIN-Plus — MAD Run

**Date:** October 2026  
**Topic:** Best method for building a personal flight search aggregator  
**Verdict:** Conditional Build — Three-Phase Approach Required

---

## Origin Story

Inspired by a real AI failure: asked to find a cheap flight, an AI gave advice to "wait for a sale" — then revealed it couldn't access flight websites because bots are blocked. The goal of this run was to find a better answer: what's the right architecture for a tool that gives a user real flight data at their fingertips?

---

## Outputs

| File | Description |
|------|-------------|
| `AA-output.md` | Advocate — strongest case FOR building a flight aggregator |
| `DA-output.md` | Devil's Advocate — strongest case AGAINST, failure modes and risks |
| `SSA-output.md` | Synthesiser — final verdict and phased build plan |
| `print.html` | PHONICSPlus-branded interactive layout (source for PDF + artifact) |
| `flight-stress-assassin-plus-MAD-Findings.pdf` | Downloadable PDF — all findings in one document |

---

## SSA Verdict (Summary)

**Conditional Build — Three-Phase Approach Required.**

| Phase | What | Time | Cost |
|-------|------|------|------|
| 1 — The Launcher | Deep-link generator: one click opens all relevant sites pre-filtered | 1 day | $0 |
| 2 — The Intelligence Layer | Amadeus API: price calendar, cheapest day, threshold alerts, trends | 1 week | $0/month (free tier) |
| 3 — The LCC Bridge | Claude-in-Chrome: authenticated session for Jetstar/AirAsia/Scoot | When needed | Optional |

**Phase 1 alone eliminates ~80% of flight search stress.**

---

## Key Debate Findings

**AA won:**
- Amadeus Self-Service API is real, free, covers 400+ full-service airlines
- Google Flights deep-link covers LCCs without any scraping
- Phase 1 (launcher) buildable in one day with zero legal risk

**DA won:**
- Full scraping is blocked industrially (Cloudflare/PerimeterX fingerprinting)
- LCCs structurally absent from GDS — Jetstar, AirAsia, Scoot not via Amadeus
- Dynamic pricing means any scraped price is a snapshot, never a guarantee
- Booking remains manual — tool kills search stress, not all stress

**SSA ruled:**
- Build the hybrid: Amadeus for full-service, deep-links for LCCs, Chrome bridge for edge cases
- 7 critical failure modes documented — avoid all of them
- Start with Phase 1 this week

---

## 7 Critical Failure Modes

1. Don't scrape without user session — will be blocked within days
2. Don't trust scraped prices as bookable — always verify on site
3. Don't try to cover all airlines on day one
4. Don't build a background scheduling service for scraping
5. Don't attempt to automate booking
6. Don't confuse "price found" with "deal confirmed" — build freshness timestamps in
7. Don't let "AI said so" replace the tool — show data source and freshness always

---

## Related

- PDF layout: `stationery/phewphonics/mad-pdf-layout-spec.md`
- PDF generator: `scripts/generate-mad-pdf.py`
- Previous run: `runs/vault-cloud-migration/`
