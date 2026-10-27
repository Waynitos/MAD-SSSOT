# AA — Advocate
## Topic: PDF BOM Column Detection — Keep Vector-Divider Architecture
## Run: 2026-10-27

---

### Position: The current vector-divider approach is correct. Fix the post-processing layer, not the detection layer.

---

### The detection works — the post-processing does not

The log confirms that `get_bom_column_dividers` finds exactly five correct divider positions on every drawing:

```
[1689.5, 1774.5, 1859.5, 1916.2, 2327.2]
```

These five x-values correctly describe the five column boundaries as drawn by Inventor in the PDF. There is nothing wrong with the vector detection approach itself. Replacing it would discard a system that is working correctly.

### The bug is entirely in build_columns_from_dividers

The function silently drops any band with no header word:

```python
if not band_words:
    continue  # <-- this line is the entire problem
```

Inventor prints "ITEM QTY" as a single merged text object. Its x-centre falls in the band `[1689.5–1774.5]`. The adjacent band `[1774.5–1859.5]` — which would be the natural QTY band — contains no header text and is silently dropped.

This is a fixable edge case, not an architectural failure.

### Fix 1: Infer QTY for narrow orphan bands after ITEM

When a band is dropped because it has no header words, check its context before discarding:

```python
if not band_words:
    # Narrow orphan immediately after an ITEM band → treat as QTY
    if columns and "ITEM" in columns[-1]["name"].upper() and (x1 - x0) < 120:
        columns.append({"name": "QTY", "x0": x0, "x1": x1,
                        "band_x0": x0, "band_x1": x1})
    continue
```

This creates the missing QTY band `[1774.5–1859.5]` from context inference rather than header text. No hardcoded coordinates needed.

### Fix 2: Split "ITEM QTY" merged headers at midpoint

When the surviving band contains "ITEM" and "QTY" in a single header text, split it:

```python
if "ITEM" in name.upper() and "QTY" in name.upper():
    mid = (x0 + x1) / 2
    columns.append({"name": "ITEM", "x0": x0, "x1": mid, "band_x0": x0, "band_x1": mid})
    columns.append({"name": "QTY",  "x0": mid, "x1": x1, "band_x0": mid, "band_x1": x1})
    continue
```

### Fix 3: Hard corruption guard in extract_bom_from_pdf

After `map_source_columns`, validate before proceeding:

```python
col_map = map_source_columns(col_names)
if col_map["Item"] is not None and col_map["Item"] == col_map["QTY"]:
    log.append(f"  WARNING: Item==QTY collision at col {col_map['Item']} — "
               f"aborting extraction for {drawing} to prevent corrupt output")
    return None
```

A blank drawing row in Excel is far better than a row containing `qty='5 12 M20'`. The user will see which drawings need manual review.

### Fix 4: Description band width guard

The band `[1859.5–1916.2]` is only 57pt wide. A multi-word description like "UPPER FLOTATION ASSEMBLY" cannot fit. After `build_columns_from_dividers`, check band widths:

```python
for col in columns:
    if "DESC" in col["name"].upper() and (col["band_x1"] - col["band_x0"]) < 150:
        # Extend leftward to absorb the QTY right edge if no data collision
        prev_right = previous_column_right_edge
        col["band_x0"] = prev_right
```

This recovers description text that was falling into the dropped orphan band.

### Why NOT to replace the architecture

1. Vector detection is working on every drawing — rewriting it risks breaking drawings that currently extract correctly.
2. The fix is localised to ~20 lines in `build_columns_from_dividers`. The rest of the pipeline (`extract_item_column`, `extract_row_cells`, `map_source_columns`, the DWG path, the Excel writer) is unaffected.
3. Non-Inventor PDFs with unknown schemas benefit from the orphan-inference logic too — it is a general improvement.
4. A schema-anchored alternative would require a parallel code path, a detector to choose between the two paths, and ongoing maintenance as new drawing templates are encountered.

### Expected outcome after fix

```
Columns detected : ['ITEM', 'QTY', 'DESCRIPTION', 'PART No. / SPECIFICATION MASS (EA)']
Column mapping   : {'Item': 0, 'QTY': 1, 'Description': 2, 'Specification': 3}
```

All 13 drawings that currently produce corrupt output should extract cleanly.

---

*AA written 2026-10-27 — RMAD cycle for PDF BOM column detection / Inventor drawing schema*
