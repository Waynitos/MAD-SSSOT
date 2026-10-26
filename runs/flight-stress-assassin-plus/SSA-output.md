# SSA Verdict — FLIGHT-STRESS-ASSASSIN-Plus

## Final Verdict
**Conditional Build — Three-Phase Approach Required.**

The goal of "never stress about flights again" is achievable — but not by building what you first imagine. The AA is right that the technical tools exist. The DA is right that full automation is a fragile, legally grey maintenance trap. The SSA reconciles both: build a hybrid tool that uses legitimate data where it's clean, browser assist where it's not, and never pretends to do what only a human can do at booking time.

---

## What the Debate Settled

| Question | AA Said | DA Said | SSA Ruling |
|---|---|---|---|
| Can we get real flight data? | Yes — Amadeus API, SerpApi | Amadeus misses LCCs; data goes stale | **Partially TRUE** — use Amadeus for trunk routes + Google Flights deep-link for LCCs |
| Does authenticated browser automation work? | Yes — user's own session bypasses bot detection | Fragile, breaks on site updates, ToS risk | **Use sparingly** — Claude-in-Chrome for specific LCC checks only, not as primary data pipeline |
| Will this eliminate flight stress? | Yes | No — booking still manual, data still stale | **Reframe the goal** — eliminate *search* stress, not all stress |
| Is this legally safe? | With user's own session, yes | ToS risk real, especially on airline sites | **Stay clean** — Google Flights deep-link + Amadeus API = zero ToS exposure |

---

## The Six Go-Conditions (Build This in This Order)

### Phase 1 — The Launcher (Build in 1 Day, Zero Legal Risk)
A tool that takes your search parameters and opens perfectly pre-filtered Google Flights, SkyScanner, and Qantas/Virgin in parallel tabs — one click, every time. No scraping. No API cost. No maintenance.

Parameters supported from day one:
- Origin / Destination
- Date range (flexible ± days)
- Max stops
- Baggage included toggle
- Departure/arrival time windows
- Airline include/exclude list
- Max price threshold

**Why this alone is worth building**: The DA's own "what would actually work" section lists this first. It's not glamorous — but it eliminates the actual stress source: re-entering the same data into five sites every time.

### Phase 2 — The Intelligence Layer (1 Week, ~$0/month)
Add Amadeus Self-Service API to give price trend data and calendar pricing:
- "What's the cheapest day in March BNE→LHR?" — answered in seconds
- Price history signal: is today's price high or low vs the last 90 days?
- Seat availability alert: price just dropped below your threshold

Limitations to communicate clearly in the UI:
- Amadeus covers full-service carriers well; Jetstar/AirAsia/Scoot shown separately via tab launcher
- Prices are indicative, not bookable — always verify on airline site before purchasing
- Free tier: 2,000 calls/month (sufficient for personal use)

### Phase 3 — The LCC Bridge (When Needed, Optional)
For low-cost carriers not in Amadeus: use Claude-in-Chrome to open and extract results from Jetstar/AirAsia while the user is already logged in. This is the authenticated-session approach the AA described — but limited to LCC price checks only, not used as a primary pipeline, and only triggered manually by the user (not on a schedule).

---

## 7 Critical Failure Modes to Avoid

1. **Don't scrape without user session** — will be blocked within days
2. **Don't trust scraped prices as bookable** — always a snapshot; verify on site before paying
3. **Don't try to cover all airlines on day one** — start with Amadeus + Google Flights; add LCC bridge incrementally
4. **Don't build a background scheduling service** — ToS exposure; use on-demand search only
5. **Don't attempt to automate booking** — last-mile is always manual; tool should hand off cleanly
6. **Don't ignore LCCs** — they're often cheapest; the Google Flights deep-link handles them cleanly without scraping
7. **Don't conflate "price found" with "deal confirmed"** — build in a one-click "verify on airline site" step before any price is acted on

---

## Architecture Decision: What Gets Built

```
FLIGHT-STRESS-ASSASSIN-Plus
│
├── LAUNCHER (Phase 1)
│   ├── Input form: origin, dest, dates, filters
│   ├── Generates deep-links for: Google Flights, Skyscanner, Qantas, Virgin, Jetstar
│   └── Opens all in parallel tabs with one click
│
├── INTELLIGENCE (Phase 2)
│   ├── Amadeus API: price calendar, cheapest day, price trend signal
│   ├── Price alert: notify when route drops below threshold
│   └── Dashboard: all active searches + alerts in one view
│
└── LCC BRIDGE (Phase 3, optional)
    ├── Claude-in-Chrome: authenticated Jetstar/AirAsia session
    ├── Manual trigger only (not scheduled)
    └── Results merged into dashboard alongside Amadeus data
```

---

## What This Delivers (Honest)

✅ Never re-enter the same search parameters again
✅ See cheapest day in a date range in seconds, not minutes
✅ Know if today's price is high or low vs recent history
✅ Get alerted when a price drops to your threshold
✅ One click opens all relevant sites pre-filtered
✅ LCC fares surfaced alongside full-service data

❌ Cannot book for you — always a manual step
❌ LCC prices may differ slightly from live site
❌ Amadeus doesn't cover every carrier
❌ Price shown ≠ price guaranteed — always verify before buying

**Net assessment**: This eliminates 80% of the friction and 100% of the "forgot to check" stress. The remaining 20% — booking, seat selection, verification — cannot be automated away without unacceptable legal and fragility risk. Build Phase 1 this week. Phase 2 next week. Phase 3 when you need it.
