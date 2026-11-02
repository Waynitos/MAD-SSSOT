# Hardware Purchase Verification Checklist
**Status:** Active | **Added:** 2026-11-03
**Applies to:** All RMAD runs involving hardware pricing (laptops, peripherals, displays, etc.)

---

## Why This Exists

During BNLP RMAD run (2026-10-24), the price cited for MacBook Pro 16" M5 Pro 48GB 1TB was **A$4,899** — sourced from third-party AU retail aggregators. The actual Apple AU price is **A$5,699** — an A$800 error (16% off).

The verdict was unaffected, but the budget reasoning in AA/DA outputs used wrong numbers. This checklist prevents that from recurring.

---

## Mandatory Steps for Hardware RMAD Runs

### 1. ✅ Price — Official Source Only
- **Always verify price directly from the manufacturer or primary retailer** (apple.com/au, microsoft.com/en-au, lenovo.com/au, etc.)
- **Never use third-party aggregators as a price source** (staticice, getpricelist, shopbot, computeralliance, etc.) — these may reflect old-gen pricing, regional retailer margins, or cached data
- If the official site is not accessible: note the source and flag the price as unverified in the output
- Record the URL and date accessed alongside any price

### 2. ✅ Spec — Confirm Exact Configuration
- Verify the exact config being priced matches the RMAD topic spec
  - CPU/chip variant, memory, storage, colour, display option
- Watch for model-line confusion (e.g., PROLED XDR vs standard Liquid Retina XDR — different product at different price)
- Watch for upgrade options already included in cart vs baseline (e.g., nano-texture glass: +A$225 to +A$1,025 depending on model)

### 3. ✅ Currency and Region
- Confirm currency is correct for the buyer's region (AUD for Australian buyer, not USD)
- Apple and others display different prices per region — verify at the regional subdomain (apple.com/au not apple.com)

### 4. ✅ Availability
- Note if the config is available to ship now vs custom order / extended wait
- Note estimated delivery window if purchase-critical

### 5. ✅ SSA Output — Price Transparency
- The SSA output must state the verified price, the source URL, and the date verified
- If price could not be verified at official source, SSA must flag this explicitly

---

## Template — Price Verification Block (for SSA outputs)

```
**Price verified:** A$X,XXX
**Source:** [URL] (apple.com/au)
**Config:** [exact spec string]
**Date verified:** YYYY-MM-DD
**Method:** Direct from official retailer — not aggregator
```

---

## What to Do If Price Cannot Be Verified

If official site is blocked or unavailable:
1. Note this explicitly in the output
2. Use best-available source and flag as unverified
3. Recommend user verify at official site before using price in decision-making
4. Do **not** present an unverified price as fact

---

## Related

- `runs/bnlp-24gb-vs-48gb/SSA-output.md` — original failure case and post-mortem
- `projects/BNLP/purchase-spec.md` — corrected BNLP purchase spec (A$5,699)
