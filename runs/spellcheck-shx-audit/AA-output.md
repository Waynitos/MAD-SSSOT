# AA Output — SpellCheck SHX/OCR Audit

**Role:** Advocate (strongest case for the current architecture)  
**MAD Run:** spellcheck-shx-audit  
**Files audited:** SpellCheckPDF_Word.py (v2026-10-23-merged-v15ag), SpellCheckOCR_Fallback.py

---

## The case for the current two-path architecture

### 1. The split is categorically correct

PDFSHX=1 (pure vector outlines, no text objects) and PDFSHX=2 (hidden searchable layer + visible outlines) are not variants of the same problem — they are different problems that happen to share a visual appearance. Treating them with a single strategy would either break the fast path for the 95% of files that have real text, or require a slow rasterisation step on every page regardless of whether it was needed.

The current design makes the right architectural call: direct text extraction everywhere it works, OCR fallback only on proven zero-text pages. This maximises throughput and keeps OCR's lower accuracy quarantined to the files that actually require it.

### 2. OCRPageProxy is an elegant integration pattern

The `OCRPageProxy` class wraps a real fitz page and substitutes OCR-derived words for `get_text("words")`, while passing everything else (insert_text, new_shape, rect, get_drawings) straight through to the real page. This means:

- **Zero modification** to any of the 12 check functions — they see PyMuPDF's standard word-tuple format regardless of where the words came from
- **Per-page activation** — the proxy wraps exactly the pages that need it, not the whole document
- **Clean fallback** — if OCR fails, the fallback continues with empty words, same as the pre-OCR behaviour

This is not an ad-hoc workaround; it is the correct application of the proxy pattern for type-compatible substitution.

### 3. Graceful degradation is implemented correctly

The import guard (`try: import SpellCheckOCR_Fallback as ocr_fallback except Exception`) captures the import error separately from the Tesseract path check. A missing Tesseract → `SKIPPED` result, not a crash. The diagnostic path in `ocr_extract_words()` distinguishes:
- Render failure
- Tesseract subprocess failure
- TSV empty
- Words found but all below confidence threshold
- Words found and returned

Each failure mode produces a specific, actionable message rather than a silent empty result. This is the right diagnostic design.

### 4. Subset-of-checks is a principled decision, not a limitation

Explicitly excluding spelling and geometry checks from `OCR_SUPPORTED_CHECK_KEYS` is the right call. OCR errors on dense small CAD text (dimensions, symbols, abbreviations) would produce spurious spelling flags at a rate that would make the report unusable. The checks that are retained — BOM sequence, project number, REV comparison, title block version — all operate on large, well-spaced, high-contrast text where OCR accuracy is genuinely reliable.

A tool that reports nothing on SHX pages is worse than useless. A tool that reports only what it can reliably verify is correct engineering.

### 5. Geometry sanity circuit-breaker handles PDFSHX=2 correctly

For PDFSHX=2 pages where AutoCAD embeds both a hidden text layer and visible vector outlines, the per-word glyph-stroke filter (both stroke endpoints inside word bbox + stroke width ≤ 0.36pt → skip) correctly identifies and discards the glyph strokes that would otherwise fire as false "line crossing" defects.

The circuit-breaker (`GEOMETRY_SANITY_MAX_FRACTION=0.05`, `GEOMETRY_SANITY_MIN_ABSOLUTE=25`) provides a safety net: if the per-word filter is overwhelmed (e.g. the entire page's geometry flags as suspicious), it treats the page as vector-outlined text and suppresses geometry checks for that page. This is correct — a page that is almost entirely glyph strokes has no real geometry to audit.

### 6. `sys.path.insert(0, _SCRIPT_DIR_EARLY)` handles deployment correctly

Engineering firms often run shared tools from a network drive with an embedded Python. Inserting the script directory at the front of `sys.path` before imports means that `SpellCheckOCR_Fallback.py` is found next to the main script regardless of how Python was invoked, without requiring the user to configure `PYTHONPATH` or install anything into the system Python.

### Honest weaknesses (acknowledged by the AA)

- `OCR_MIN_CONFIDENCE = 40` was set empirically and has not been calibrated against the actual distribution of project code recognition confidence
- `OCR_DPI = 300` is adequate for most title block text but marginal for the smallest CAD annotations (≤ 2mm)
- The zero-text trigger has no way to distinguish a genuine SHX page from a blank page or a page that is entirely an embedded raster image
- The 0.36pt stroke-width threshold was calibrated on one specific AutoCAD configuration
- Spelling is completely absent for PDFSHX=1 pages — this is a known gap, not a bug, but it is the single biggest functional limitation

*AA output — SpellCheck SHX audit MAD cycle*
