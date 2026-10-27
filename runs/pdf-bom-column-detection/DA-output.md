# DA — Devil's Advocate
## Topic: PDF BOM Column Detection — Against Current Spatial-Heuristic Architecture
## Run: 2026-10-27

---

### Position: The architecture is fundamentally wrong for a known-schema problem. The 100% failure rate is the signal.

---

### 100% failure is not an edge case

The log shows every single drawing with a BOM fails in exactly the same way. This is not a fixable edge case — it is the system's **expected output** for Inventor PDFs. A diagnostic metric of 0/13 success is not "working detection with a post-processing bug." It is a system that does not work for its primary use case.

The correct response to a 100% failure rate is to examine the assumption that justifies the architecture, not to patch the output.

### The core assumption is wrong for Inventor PDFs

The vector-divider approach assumes:
> "Each column has a header word that falls within its divider band."

Inventor PDFs violate this assumption by design. The ITEM and QTY columns share a single merged header cell. This is not unusual in engineering drawing templates — it is a common space-saving convention. Any generalised spatial-heuristic that relies on header-word-to-band correspondence will fail whenever a drawing uses merged headers.

Patching `build_columns_from_dividers` to infer QTY from context is not a fix — it is teaching the function to guess. Guesses accumulate errors.

### The missing band contains the description data

This is the critical finding the AA approach underweights. The band `[1774.5–1859.5]` that is silently dropped is not just missing a QTY column. It is the **left portion of the Description column's data zone**.

Actual description data layout in the drawings:
- "UPPER FLOTATION ASSEMBLY" — the word "UPPER" starts at approximately x=1780, well inside the dropped band
- "HEX HEAD BOLT" — "HEX" starts at approximately x=1777
- The surviving description band `[1859.5–1916.2]` is 57pt wide — wide enough for exactly one short word

The current code does not just produce wrong QTY values. It **discards the majority of every description cell**. This is invisible in the log because the code reports what it found, not what it missed.

### extract_item_column already has the answer

`extract_item_column()` correctly finds every item number in the ITEM column. It knows the exact x-coordinates of the ITEM column header (`hx0`, `hx1`). This is reliable, proven information.

The DESCRIPTION column header word is also reliably findable — `find_bom_headers()` locates it to place the header row. Its x-coordinate is `desc_header_x0`.

These two known anchors define all four columns unambiguously:
- ITEM band: `[item_hx0 - margin, item_hx1 + margin]`
- QTY band: `[item_hx1 + margin, desc_hx0 - margin]`
- DESCRIPTION band: `[desc_hx0 - margin, spec_hx0 - margin]`
- SPECIFICATION band: `[spec_hx0 - margin, page_right]`

No orphan inference. No width guards. No merged-header splitting. Just the two header words the system already finds, used to derive all band boundaries directly.

### The dividers are supplementary data, not primary data

The vector dividers correctly identify WHERE the column boundaries are drawn. But for a known-schema PDF template, the drawn boundaries are a consequence of the column layout — not the source of truth for it. Using the dividers as the primary driver means the column layout can only be inferred after the fact, with all the ambiguity that entails.

For Inventor PDFs, the drawn lines confirm what the header words already tell us. Use the header words as primary anchors and the dividers as validation, not the reverse.

### The correct fix

Add a schema-anchored path in `extract_bom_from_pdf`, activated when `get_bom_column_dividers` returns ≥3 dividers AND the header row contains both an ITEM word and a DESCRIPTION word:

```python
def build_columns_from_headers(item_header_word, desc_header_word, 
                                spec_header_word, mass_header_word=None):
    """
    Derive column bands from header word x-coordinates.
    Works for any Inventor PDF regardless of merged-header layout.
    """
    item_x1 = item_header_word[2] + COLUMN_MARGIN_PT
    desc_x0 = desc_header_word[0] - COLUMN_MARGIN_PT
    spec_x0 = spec_header_word[0] - COLUMN_MARGIN_PT
    mass_x0 = mass_header_word[0] - COLUMN_MARGIN_PT if mass_header_word else 99999
    
    return [
        {"name": "ITEM",          "band_x0": 0,       "band_x1": item_x1},
        {"name": "QTY",           "band_x0": item_x1, "band_x1": desc_x0},
        {"name": "DESCRIPTION",   "band_x0": desc_x0, "band_x1": spec_x0},
        {"name": "SPECIFICATION", "band_x0": spec_x0, "band_x1": mass_x0},
    ]
```

Keep `build_columns_from_dividers` as the fallback for PDFs where the header-word path fails (non-Inventor, custom templates, degraded text layer).

### What "targeted patches" will actually look like

The AA's Fix 1 (infer QTY from orphan context) requires:
- Knowing the previous column was ITEM
- Knowing the orphan width threshold (120pt — why 120? what if Inventor changes its template?)
- Correctly identifying which orphan band to promote vs which to skip (row-number gutters also create orphan bands)

The AA's Fix 4 (extend description band leftward) requires:
- Knowing what "too narrow" means (150pt threshold — derived how?)
- Not colliding with the QTY band's data
- Handling the case where the orphan band was NOT inferred as QTY (Fix 1 and Fix 4 are coupled)

Each threshold is a hardcoded guess that will break on the next drawing template that doesn't match Inventor's current layout. The schema-anchored approach has no thresholds — it uses the actual header word positions.

### Silent corruption is a safety issue for engineering BOMs

The current output `qty='5 12 M20'` in a BOM that drives physical fabrication orders is not just a quality problem. An incorrect quantity on a structural bolt BOM could have real consequences. The architecture should never permit silent data corruption. A hard failure with a clear error message is always better than a quietly wrong number in a cell.

---

*DA written 2026-10-27 — RMAD cycle for PDF BOM column detection / Inventor drawing schema*
