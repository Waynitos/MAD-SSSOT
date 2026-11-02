# SSA Verdict — BNLP: 24GB vs 48GB Unified Memory
**Run date:** 2026-10-24 | **Project:** BNLP | **Trigger:** RMAD

---

## Verdict: 48GB — A$5,699 *(corrected from A$4,899 — see Process Note)*

### Verdict Table

| Dimension | Winner | Notes |
|---|---|---|
| macOS-native AI / Claude | 🟡 Tie | Both fine; 24GB genuinely sufficient |
| Inventor via Parallels | 🔴 48GB | 24GB leaves ~10-12GB for macOS after VM + OS cut |
| Local LLM inference | 🔴 48GB | 17GB vs 35GB usable — meaningful capability cliff |
| Future-proofing (5yr) | 🔴 48GB | Non-upgradeable + apps getting heavier |
| Budget efficiency | 🟢 24GB | Real saving; ~$120/yr amortised |
| Risk profile | 🔴 48GB | Asymmetric — no downside to more RAM; real downside to less |

**Score: 48GB wins 4–1 (1 tie)**

### Key Drivers
- RAM is sealed for life — asymmetric risk strongly favours more
- Parallels dual-workload (Inventor VM + macOS AI work simultaneously) is the exact pressure case where 24GB struggles
- Local LLM ceiling: 14B max on 24GB vs 32B on 48GB — meaningful for an AI-primary machine
- $120/year amortised over 5 years is not a meaningful saving on a A$5,699 machine

### Win-Wins
- Parallels Desktop license (~A$150/yr) — budget regardless of config
- AppleCare+ (~A$299) — strongly recommended on a sealed, non-upgradeable device
- Consider whether Inventor on Mac will be frequent or rare — if rare, 24GB is defensible

---

## ⚠️ Process Note — Price Accuracy Failure

**Issue:** During this RMAD run, the price cited for the 48GB model was **A$4,899** (sourced from third-party AU retailer listings). The actual Apple AU price confirmed at point of purchase is **A$5,699** — a **A$800 discrepancy**.

**Root cause:** AA and DA agents relied on aggregator/retailer sites rather than verifying price directly from apple.com/au. Third-party listings may reflect:
- Older generation pricing
- Regional retailer margins (below or above RRP)
- Cached/outdated data

**Impact on verdict:** The 48GB decision stands — the SSA verdict is unchanged. However, the price used in the MAD reasoning was materially wrong, which could have affected budget planning.

**Fix:** See `checklists/hardware-purchase-verification.md` — price verification step added as mandatory for all hardware RMAD runs.
