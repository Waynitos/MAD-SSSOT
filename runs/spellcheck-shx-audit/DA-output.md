# DA Output — SpellCheck SHX/OCR Audit

**Role:** Devil's Advocate (strongest case against the current implementation)  
**MAD Run:** spellcheck-shx-audit  
**Files audited:** SpellCheckPDF_Word.py (v2026-10-23-merged-v15ag), SpellCheckOCR_Fallback.py

---

## The case against: seven structural weaknesses

### 1. Tesseract is called with no PSM flag — the default is wrong for CAD

`run_tesseract_tsv()` calls:
```python
[tesseract_exe, image_path, output_base, "tsv"]
```

No `--psm` flag means Tesseract defaults to PSM 3: "Fully automatic page segmentation, but no OSD." PSM 3 looks for column structures and multiple text regions across the full page. A CAD title block is the opposite: isolated fields widely spaced on what is mostly white space (the drawing area). PSM 3 will attempt to fit these isolated strings into a column layout, group unrelated fields together, and mis-segment text that appears near drawing elements.

The correct mode for CAD title blocks is **PSM 11: sparse text** — "Find as much text as possible in no particular order." PSM 11 is specifically designed for pages where text is isolated and not arranged in a conventional document layout. This is exactly what a title block is.

**Impact**: PSM 3 will reliably miss or merge title block fields that PSM 11 would find. Project number checks, REV checks, and BOM checks on SHX pages are failing to find tokens that are actually present in the image.

### 2. No `--oem` flag and no `-l` flag degrade accuracy further

OEM 3 (default) runs both the legacy Tesseract engine and the LSTM engine. For clean rasterised images (a PDF page at 300 DPI is considerably cleaner than a scanned document), OEM 1 (LSTM only) is faster and more accurate. OEM 3 produces conflicting candidates from the two engines and is noisier on clean inputs.

No `-l` flag means Tesseract uses `eng` by default — but the English language model actively penalises alphanumeric codes that don't appear in its training corpus. A project number like `PJ00193` or a drawing reference like `AB-1234-001` will have its per-character confidence scores pulled down by the language model's expectation that these character sequences are unlikely. This pushes their Tesseract confidence scores below `OCR_MIN_CONFIDENCE = 40`, and they are **silently dropped**.

The project-number check is in `OCR_SUPPORTED_CHECK_KEYS`. On SHX drawings, that check is almost certainly reading empty results because the project number is being discarded by the confidence filter — not because OCR failed to read it.

### 3. The zero-text trigger fires on pages it shouldn't

`len(page.get_text("words")) == 0` triggers OCR fallback. This is the correct heuristic for SHX pages, but it also fires on:

- **Blank continuation sheets** — these exist in all multi-sheet drawing packages; the second and third sheets of a title block series often have continuation borders with no text
- **Cover sheets with only a logo** — a company logo embedded as a raster image; zero text words, but OCR will read the logo and report garbled findings
- **Inventor drawings with rasterised borders** — Autodesk Inventor exports can embed the border as an image layer with the title block text elsewhere; some configurations produce a zero-text first page
- **Mixed-mode drawing packages** — PDF packages where pages from different sources are combined; a scanned legacy sheet in the middle of an otherwise digital package

On all of these, OCR will either find nothing and report an unexplained empty result, or find garbage (logo text, border label fragments) and report it as real. There is no distinction between "SHX page" and "intentionally sparse page" in the current code.

### 4. `OCRPageProxy` is incomplete — `get_text("dict")` is not intercepted

`OCRPageProxy.get_text()` intercepts `get_text("words")` but passes all other variants to `self._real_page.get_text(kind)`. For a zero-text SHX page, `get_text("dict")` returns empty blocks.

In `SpellCheckPDF_Word.py`, `identify_rotated_lines()` and `map_line_directions()` both call `page.get_text("dict")`. These functions are called from geometry paths that are in `OCR_SUPPORTED_CHECK_KEYS`? No — they are excluded today. But:

1. The proxy's contract is incomplete — any future check added to `OCR_SUPPORTED_CHECK_KEYS` that uses the dict path will silently get empty data, with no error and no diagnostic
2. The comments in the code do not document this constraint — a developer adding a new check to the OCR-supported set would not know that dict-path functions don't work

This is a **latent bug**: not causing failures today only because of the current check exclusion list, not because the code is correct.

### 5. The 0.36pt stroke-width filter is calibrated on one AutoCAD configuration

The per-word glyph-stroke filter (`stroke width ≤ 0.36pt + both endpoints inside word bbox`) was calibrated on a specific AutoCAD configuration. ISO 704 and ASME Y14.2 lineweight standards specify:

- Text layer (for title block text): 0.25mm = **0.71pt** — nearly double the filter threshold
- Dimension layer: 0.18mm = **0.51pt** — still above threshold

Any drawing produced following ISO or ASME lineweight standards will have SHX glyph strokes above the 0.36pt filter. These strokes bypass the per-word filter entirely and saturate the geometry sanity circuit-breaker instead. When the circuit-breaker fires, ALL geometry checks are suppressed for that page — including genuine line crossings that exist alongside the glyph strokes.

The result is silent suppression of real defects on any drawing using standard lineweights.

### 6. Spelling is 100% absent on PDFSHX=1 — the tool's primary function fails on a common input

The tool is named `SpellCheckPDF_Word.py`. Its primary stated function is spell checking engineering drawing PDFs. `OCR_SUPPORTED_CHECK_KEYS` does not include any spelling check. This means:

On every SHX-font drawing where AutoCAD exported with PDFSHX=1 (the legacy default before AutoCAD 2016 changed the default; still common in older drawing sets and firms using older AutoCAD configurations), the spell check delivers zero spelling findings. Not "fewer findings" — zero. A drawing with "COMPRESSOR INSTALATION" in its title block on an SHX page passes the spell check with no flags.

The AA's argument that spelling on OCR text is too noisy is correct in principle for dense small text. Title block content — the drawing title, revision descriptions, note headers — is large, well-spaced, high-contrast text. This is exactly the content where OCR spell-checking is feasible. The current architecture permanently excludes it by design rather than attempting it with appropriate calibration.

### 7. `page.get_textpage_ocr()` already exists in PyMuPDF — the entire pipeline is duplicated

PyMuPDF has provided `page.get_textpage_ocr()` since version 1.21.0 (November 2022). This built-in method:
- Renders the page to a pixmap internally (no temp files)
- Calls Tesseract via C bindings (no subprocess)
- Returns a proper `TextPage` with word-level coordinates already in PDF point space
- Accepts DPI and language parameters

The entire `SpellCheckOCR_Fallback.py` — `render_page_to_image()`, `run_tesseract_tsv()`, `tsv_rows_to_word_tuples()`, coordinate scaling, TSV parsing, temp file management, `find_tesseract_exe()`, `TesseractPath.txt` — duplicates what PyMuPDF already provides natively.

The one advantage of the current approach is that it gives explicit control over the Tesseract subprocess arguments (`--psm`, `--oem`). With `get_textpage_ocr()`, PSM/OEM are passed as a combined integer flags parameter. This is less ergonomic but is documented and works. The duplication cost (maintenance surface, temp file races on shared servers, subprocess overhead on every SHX page) is not justified by this ergonomic difference.

The correct fix is not "add `--psm 11` to the subprocess call" — it's "replace the subprocess pipeline with `get_textpage_ocr()` and pass the flags parameter."

### 8. `OCR_MIN_CONFIDENCE = 40` — wrong in both directions simultaneously

A threshold of 40 is:
- **Too low** for standard English text: a confidence of 40–49 on a clearly printed word indicates genuine ambiguity or image quality degradation. Passing these into BOM sequence or REV description checks adds noise.
- **Too high** for alphanumeric codes: as described in weakness 2, project numbers and drawing references are penalised by the English language model and score in the 30–45 range even when correctly read. A threshold of 40 drops the correctly-read codes.

No amount of tuning a single threshold resolves both directions simultaneously. The fix requires two thresholds: a higher one for dictionary-word text (REV descriptions, note text, BOM descriptions) and a lower one for code-pattern text (project numbers, drawing numbers, item references).

### 9. 300 DPI is insufficient for the text sizes this tool targets

`OCR_DPI = 300` renders the page at 300 pixels per 72 points. A title block field in 2.5mm text (common in BS/ISO/DIN engineering drawing standards) renders at:

- 2.5mm ÷ (25.4mm/300px) = **29.5 pixels tall**

Tesseract's LSTM engine is documented to give reliable recognition above 30 pixels character height. 300 DPI is right at the floor, meaning the slightest deviation in character proportion, stroke width variation, or rendering anti-aliasing drops below reliable recognition.

400 DPI renders 2.5mm text at 39.4 pixels — well above the floor with clear margin.

The render cost increase from 300 to 400 DPI is ~78% (area scales as DPI²), but OCR fallback only runs on zero-text pages — a small fraction of pages in a typical drawing package. A 78% increase in render time for a path that runs 5% of the time is not a meaningful throughput concern.

*DA output — SpellCheck SHX audit MAD cycle*
