# MAD Run — BNLP: 24GB vs 48GB Unified Memory
**Project:** BEEXCITED NEW LAPTOP PROJECT (BNLP)
**Run date:** 2026-10-24 | **Trigger:** RMAD | **Session:** https://claude.ai/code/session_01Qtgmg2S6xYxB6utagdJhGn

---

## Summary

Full MAD cycle on whether to configure the MacBook Pro 16" M5 Pro with 24GB or 48GB unified memory.

**Verdict: 48GB wins 4–1** — decision locked 2026-10-24.

---

## Files

| File | Content |
|------|---------|
| `AA-output.md` | Advocate — strongest case FOR 24GB |
| `DA-output.md` | Devil's Advocate — strongest case AGAINST 24GB (= for 48GB) |
| `SSA-output.md` | Synthesiser verdict with scoring table and process note |

---

## Decision Locked

**MacBook Pro 16" M5 Pro 48GB 1TB Space Black — A$5,699 (Apple AU)**

Key drivers:
- RAM is non-upgradeable — asymmetric risk strongly favours more
- Parallels dual-workload (Inventor VM + macOS AI work) is the pressure case where 24GB struggles
- Local LLM ceiling: 14B max on 24GB vs 32B on 48GB
- $120/year amortised over 5 years is not a meaningful saving

---

## ⚠️ Post-Run Process Failure — Price Accuracy

**What went wrong:** During the RMAD run, pricing was sourced from third-party AU retailer aggregators. The price cited in AA/DA reasoning was **A$4,899**. The actual Apple AU price for MBP 16" M5 Pro 48GB 1TB is **A$5,699** — an **A$800 discrepancy**.

**Why it matters:** The verdict was not affected (48GB still wins), but the budget reasoning used wrong numbers. On a higher-stakes decision (e.g., a comparative purchase where price is a deciding factor), this error could produce a wrong answer.

**Root cause:** AA/DA agents did not verify price at apple.com/au. Third-party listings can reflect:
- Old-generation pricing indexed by search
- Below/above-RRP retailer margins
- Cached data from price comparison aggregators

**Fix implemented:** `checklists/hardware-purchase-verification.md` — mandatory direct-source price verification step added for all hardware RMAD runs.

---

## Related Files

- `projects/BNLP/purchase-spec.md` — full cart spec with corrected price
- `checklists/hardware-purchase-verification.md` — process fix
