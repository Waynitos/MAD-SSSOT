# DA Output — FLIGHT-STRESS-ASSASSIN-Plus

## Verdict
**The dream of "never stress about flights again" will be replaced by a new stress: maintaining a fragile, legally grey tool that breaks every time an airline updates its website, changes its API terms, or detects your session.**

---

## Critical Blockers

**1. Bot detection is industrial-grade and actively maintained**
Qantas, Emirates, Singapore Airlines, Jetstar, Virgin Australia — every major carrier uses Cloudflare, Akamai Bot Manager, or PerimeterX. These systems fingerprint: browser canvas rendering, WebGL signatures, mouse movement entropy, keystroke timing, TLS fingerprint (JA3 hash), IP reputation, and behavioural patterns. A Playwright/Puppeteer session is detectable within seconds even with stealth plugins. The cat-and-mouse arms race never ends — the airlines pay full-time engineers to stay ahead of it.

**2. Dynamic pricing means data is stale before you read it**
Flight prices can change every 30–90 seconds based on seat class inventory, demand signals, competitor pricing, and time-of-day algorithms. A price you scraped 2 minutes ago may not be bookable at that price. The "real data" the user wants is a moving target — you're always seeing a snapshot, never the truth. Google Flights itself shows prices that disappear when you click through.

**3. The user cannot actually book through this tool**
Even if aggregation works perfectly, the booking still happens on the airline or OTA site. The tool eliminates search stress but not decision and booking stress — and the handoff from tool to booking site reintroduces every friction point: seat selection, baggage options, payment, confirmation emails, check-in links. The "never stress again" promise breaks at the last mile.

**4. GDS/aggregator access is not available at personal scale**
Amadeus, Sabre, and Travelport (the systems that power Expedia, Booking.com, etc.) require travel agency accreditation or enterprise contracts. Amadeus Self-Service API exists but: rate limits are severe (2,000 calls/month free tier), coverage is incomplete (low-cost carriers like Jetstar, Scoot, AirAsia often excluded or stale), and pricing returned is not always the same as what you'd get booking directly.

**5. Low-cost carrier data is structurally inaccessible**
Ryanair, Jetstar, Scoot, AirAsia — the carriers most likely to have the cheapest fares — are NOT in GDS systems. They sell direct-only or through select OTAs with custom arrangements. Any aggregator that doesn't cover LCCs is missing the exact fares that justify the tool's existence.

---

## Why Every Obvious Solution Fails

**Official APIs (Amadeus, Skyscanner):**
- Skyscanner API: closed to new partners since 2019 for most use cases; waitlist, no personal use
- Amadeus Self-Service: covers ~60% of global inventory, excludes most LCCs, 2,000 calls/month free (one search = multiple calls), $0.002–0.006/call after that, data freshness 15–30 minutes
- Google Flights API: does not exist publicly; the QPX Express API was shut down in 2018

**Scraping airline sites directly:**
- Cloudflare challenge pages stop headless browsers cold
- Dynamic JavaScript rendering means the price isn't in the HTML — it's loaded after 3–5 API calls the browser makes with authenticated session tokens
- Airlines actively monitor for patterns: too many searches from one IP = block; rotating proxies = expensive and detectable via fingerprinting

**Browser automation with user's logged-in session:**
- Fragile: a site update (new DOM structure, new anti-bot layer, new checkout flow) breaks the script silently
- Requires the user to keep browsers open and authenticated constantly
- Session tokens expire; re-authentication flows often involve CAPTCHAs or 2FA that automation can't handle
- Violates ToS of virtually every airline and OTA

**Hybrid "AI watches the screen for you" approach:**
- Computer vision on booking sites is slow (3–8 seconds per search), error-prone on dynamic content, and still can't handle CAPTCHAs
- Requires the user's machine to be running and logged in — not a background service

---

## The Maintenance Nightmare

Every airline website redesign (happens every 18–24 months on average) breaks scrapers silently. The user must detect the breakage, diagnose which site broke, reverse-engineer the new structure, rewrite and test, redeploy. This is a part-time job. Multiply by every airline, every OTA, every price comparison site. Professional flight data companies employ teams of engineers to maintain this infrastructure. A solo personal tool will always be weeks behind.

---

## What the User Will Still Do Manually

Even with a perfect aggregator working:
- **Verify the price is still live** — must click through to the airline site before trusting any displayed price
- **Compare baggage inclusions** — not a boolean; varies by fare class, route, and booking channel
- **Handle award/points fares** — no aggregator surfaces Qantas Points or Velocity Points pricing
- **Choose seats** — seat maps are not aggregatable
- **Book** — always manual, always on the airline/OTA site

---

## The Legal & ToS Minefield

- Qantas, Virgin Australia, Emirates ToS all explicitly prohibit automated access, screen scraping, and data extraction. Violation = account termination risk (loyalty points gone), IP ban, and potential legal action.
- Computer Fraud and Abuse Act (US) / equivalent Australian law: Automated access to systems that prohibit it in their ToS has been litigated as unauthorised access.
- Some airlines have GDS agreements that prohibit display of their fares outside authorised channels.

---

## What WOULD Actually Work (Residual Honest Assessment)

1. **Google Flights deep-link generator** — construct perfect Google Flights URLs with all parameters pre-filled. User clicks one link, lands on pre-filtered results. Legally clean, always fresh, zero maintenance.
2. **Fare alert aggregation** — parse official fare alert emails from Google Flights, Skyscanner, Hopper into one dashboard. No scraping, no ToS issues.
3. **Amadeus Self-Service for trunk routes** — for major routes (BNE-LHR, SYD-SIN), covers 80%+ of full-service carrier inventory. Good for price trend signals within free tier.
4. **Scheduled browser bookmark launcher** — opens all relevant pre-filtered searches in parallel tabs with one click. Zero maintenance, legally clean.

None of these deliver "never stress again." They deliver "stress less, search smarter."
