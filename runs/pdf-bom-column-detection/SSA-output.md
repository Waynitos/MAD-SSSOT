# SSA — Synthesiser Verdict
## Topic: PDF BOM Column Detection — Inventor Drawing Schema
## Run: 2026-10-27

---

### Verdict: Hybrid fix — targeted surgery, not architectural replacement

The AA and DA have reached compatible conclusions through different lenses. The SSA resolves the apparent tension between them by observing that they are arguing about **different layers of the same problem**.

---

### What the evidence says unambiguously

The log shows a **100% failure rate** across all 13 BOM drawings in the batch. This is not an edge case. The divider positions are identical on every drawing:

```
[1689.5, 1774.5, 1859.5, 1916.2, 2327.2]
```

The five dividers correctly describe the five column boundaries. The detection works. The failure is entirely in **post-detection processing** — specifically, two coupled bugs:

**Bug 1 — Orphan band dropped silently:**  
`build_columns_from_dividers` skips any band with no header word. The band `[1774.5–1859.5]` (85pt wide) contains no header word because Inventor prints "ITEM QTY" as a single merged text object centred in the `[1689.5–1774.5]` band. The orphan band is silently discarded.

**Bug 2 — Description data lives in the dropped band:**  
The band `[1774.5–1859.5]` that is silently dropped is not empty. It is the left portion of the Description column's data zone. Most multi-word description text physically starts here. The band `[1859.5–1916.2]` (57pt) that *does* survive is far too narrow to hold "UPPER FLOTATION ASSEMBLY" — it captures at most one word.

**Bug 3 — Duplicate column mapping causes data corruption:**  
After `build_columns_from_dividers` drops the orphan band, `map_source_columns` sees `col_names[0] = "ITEM QTY"`. Both `find(["ITEM"])` and `find(["QTY", "QUANTITY"])` match at index 0. The result `{'Item': 0, 'QTY': 0}` causes `extract_row_cells` to cram item number + qty into one cell, and the QTY digit lands in the Description column.

---

### Where AA and DA agree (and where they diverge)

**Both agree:**
- The five dividers are correct; vector detection is not the problem
- `extract_item_column()` already works and provides reliable ITEM x-coordinates
- The orphan band must not be dropped
- Silent data corruption is unacceptable; a guard is needed

**AA's contribution:** The architecture is sound; the fixes are surgical and localised to `build_columns_from_dividers` and `map_source_columns`.

**DA's contribution:** The orphan band is not just a QTY band — it is the *left portion of the Description data zone*. The description band must be treated as `[1774.5–1916.2]`, not `[1859.5–1916.2]`. The DA correctly identifies that fixing only the ITEM/QTY split without also merging the description bands would still produce truncated descriptions.

**DA's schema-anchoring proposal** (replace `build_columns_from_dividers` for Inventor PDFs) is the right diagnosis but unnecessary surgery. The same result can be achieved by fixing `build_columns_from_dividers` to handle orphan bands correctly — which also repairs the description data loss.

---

### SSA Decision: Three targeted fixes, applied in this order

#### Fix 1 — Never silently drop orphan bands

In `build_columns_from_dividers`, when a band has no header word and is narrower than a threshold (say 120pt), infer its purpose from its left neighbour:

```python
if not band_words:
    # Orphan band — don't discard; infer from left neighbour
    if columns and columns[-1]["name"].upper() in ("ITEM", "ITEM NO", "ITEM QTY"):
        # Narrow orphan immediately after ITEM band → this is the QTY band
        if (x1 - x0) < 120:
            columns.append({"name": "QTY", "x0": x0, "x1": x1,
                            "band_x0": x0, "band_x1": x1})
    continue  # wider orphans still skipped (row-number gutters)
```

This correctly creates a `QTY` band for `[1774.5–1859.5]` without requiring header text.

#### Fix 2 — Merge description band to include orphan left portion

When `map_source_columns` detects `col_map["Item"] == col_map["QTY"]` (the corruption sentinel), fall back to treating the band immediately after ITEM as QTY and extending the following band leftward to absorb the orphan.

More robustly: after `build_columns_from_dividers`, if a column named "ITEM QTY" exists, **split it at its midpoint** → ITEM (left half) + QTY (right half), then extend the next column's `band_x0` leftward to the split point. This keeps description data that was landing in the now-split right half.

#### Fix 3 — Hard guard in map_source_columns

```python
col_map = map_source_columns(col_names)
if col_map["Item"] is not None and col_map["Item"] == col_map["QTY"]:
    log.append(f"  WARNING: ITEM and QTY mapped to same column ({col_map['Item']}) — "
               f"data would be corrupt; attempting schema recovery")
    # attempt recovery: look for "ITEM QTY" merged header and split
    # ... (recovery logic) ...
    if recovery_failed:
        log.append(f"  ERROR: Column recovery failed — skipping drawing {drawing}")
        return None  # hard stop; blank row is better than corrupt data
```

A drawing that cannot be safely extracted should produce no rows, not corrupt rows. The user can identify and handle it manually.

---

### Summary of recommended code changes in BomExtractorSweeper.py

| Function | Change |
|---|---|
| `build_columns_from_dividers` | Infer "QTY" for narrow orphan bands following ITEM; split "ITEM QTY" merged headers at midpoint; extend description band leftward |
| `map_source_columns` | No logic change needed if Fix 1 works; keep as final safety net |
| `extract_bom_from_pdf` | Add guard: if `col_map["Item"] == col_map["QTY"]`, log warning + attempt recovery, hard-stop if recovery fails |

---

### What NOT to do

- Do **not** replace `build_columns_from_dividers` with a schema-anchored Inventor-specific path. The generalised fix is cleaner, handles any PDF that uses merged headers, and does not require maintaining a parallel code path.
- Do **not** hardcode the Inventor divider coordinates `[1689.5, 1774.5, …]`. They happen to be consistent across this batch, but that is an artefact of Inventor's fixed template — a different sheet format would break a hardcoded lookup.
- Do **not** rely on `extract_item_column()` x-coordinates to drive column detection. That function works well for its purpose (finding item rows), but coupling column detection to it would create a circular dependency and make the code harder to maintain.

---

### Risk rating of the fix

**Low.** All three changes are additive guards. The only behavioural change to passing drawings is that orphan bands are now named "QTY" (where previously they were silently dropped and the header fell into the previous band). Drawings without merged headers are unaffected.

---

*SSA written 2026-10-27 — RMAD cycle for PDF BOM column detection / Inventor drawing schema*
