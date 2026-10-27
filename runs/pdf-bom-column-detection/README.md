# RMAD Run — PDF BOM Column Detection / Inventor Drawing Schema
**Date:** 2026-10-27  
**Project:** BOM Extractor Sweeper (PDF-ACAD-INVENTOR CLEAN SWEEPER)  
**Trigger:** User observed 100% failure on PDF BOM extraction — column corruption in Excel output

---

## Problem Statement

The BOM Extractor script (BUILD: `2026-10-16-bom-extractor-v38`) extracts Bill of Materials data from Inventor-generated PDFs. A real production run on project **PJ00201-GTA-3450** (32 PDFs, 13 with BOMs) produced:

- **Column mapping corrupt on every drawing:**  
  `{'Item': 0, 'QTY': 0, 'Description': 1, 'Specification': 2}`  
  (Item and QTY both mapped to column 0)

- **Quantity cells contained mixed data:**  
  `qty='5 12 M20'` — item number + qty + description word concatenated

- **Descriptions missing or truncated:**  
  `desc='HEAD'` when full text should be "HEX HEAD BOLT"

**Root cause:** Inventor PDFs print "ITEM QTY" as a merged header text in a single band. The divider at x≈1774.5 creates an orphan band [1774.5–1859.5] with no header word. `build_columns_from_dividers` silently drops orphan bands. The dropped band is also where the majority of description cell data physically lives.

---

## MAD Outputs

| File | Position |
|---|---|
| [AA-output.md](AA-output.md) | Keep vector-divider architecture; apply targeted fixes to `build_columns_from_dividers` |
| [DA-output.md](DA-output.md) | Replace column detection with schema-anchored header-word approach for Inventor PDFs |
| [SSA-output.md](SSA-output.md) | Synthesiser verdict — hybrid: surgical fixes, not architectural replacement |

---

## SSA Decision Summary

**Three targeted fixes to `build_columns_from_dividers` and `extract_bom_from_pdf`:**

1. **Never silently drop orphan bands** — infer "QTY" for narrow bands (< 120pt) immediately following an ITEM column
2. **Split merged "ITEM QTY" headers** at midpoint → separate ITEM and QTY bands; extend next column's `band_x0` leftward to absorb the split right half
3. **Hard corruption guard** — if `col_map["Item"] == col_map["QTY"]` after mapping, log warning and return `None` (blank rows in Excel, not corrupt data)

**Expected result after fix:** All 13 drawings that currently produce corrupt output should produce clean `{'Item': 0, 'QTY': 1, 'Description': 2, 'Specification': 3}` mappings with full description text.

---

## Files in this run

```
runs/pdf-bom-column-detection/
  README.md         ← this file
  AA-output.md      ← Advocate: keep architecture, patch post-processing
  DA-output.md      ← Devil's Advocate: replace with schema-anchored detection
  SSA-output.md     ← Synthesiser: hybrid targeted fixes
```

---

*RMAD run completed 2026-10-27*
