# SSA Output — SpellCheck SHX/OCR Audit

**Role:** Synthesizer (tested verdict + fix proposal)  
**MAD Run:** spellcheck-shx-audit  
**Files audited:** SpellCheckPDF_Word.py (v2026-10-23-merged-v15ag), SpellCheckOCR_Fallback.py

---

## A. Verdict: What Held Up, What Didn't

| Claim | Verdict | Reasoning |
|---|---|---|
| AA: Two-path split (PDFSHX=1 OCR / PDFSHX=2 direct) is architecturally correct | **CONFIRMED** | The underlying problem separation is sound — one path has text, one doesn't; OCR is the only option for PDFSHX=1. |
| AA: OCRPageProxy integration pattern is elegant | **PARTIALLY CONFIRMED** | Elegant for `get_text("words")` consumers but silently wrong for any consumer calling `get_text("dict")` — the proxy is incomplete. |
| AA: Graceful degradation on missing Tesseract / import error | **CONFIRMED** | Import error captured in `_ocr_import_error`, distinct from empty OCR result. Tool continues correctly. |
| AA: Sanity circuit-breaker correctly handles PDFSHX=2 glyph-stroke saturation | **PARTIALLY CONFIRMED** | Circuit-breaker fires correctly when saturation occurs, but if the 0.36pt filter fails (wrong pen width), circuit-breaker fires instead of filter — suppressing real crossings without the user knowing why. |
| AA: Subset-of-checks for OCR is correct | **CONFIRMED** | Skipping spelling and geometry on OCR'd CAD text is the right call. Dense small text on rasterised CAD is too noisy for Tesseract. |
| DA: No `--psm` flag → PSM 3 wrong for CAD title block layout | **CONFIRMED** | PSM 3 expects column layout. Isolated title block fields widely spaced on a mostly-empty strip are exactly what PSM 11 (sparse text) is designed for. This is a real, concrete failure mode. |
| DA: No `--oem` flag → OEM 3 noisier than OEM 1 | **CONFIRMED** | OEM 1 (LSTM only) is faster and more accurate on clean images. OEM 3 adds legacy engine noise. No reason not to specify it. |
| DA: No `-l` flag → project codes penalised by English language model | **CONFIRMED** | Tesseract's LSTM language model penalises alphanumeric codes like `PJ00193` that don't appear in English text corpora. `conf < 40` for project codes is a real risk, not theoretical. |
| DA: Zero-text trigger unreliable (blank pages, logo-only, mixed-mode) | **CONFIRMED** | No heuristic exists to distinguish "SHX page" from "intentionally blank page" — confirmed failure mode. |
| DA: OCRPageProxy `get_text("dict")` unpatched = latent bug | **CONFIRMED** | `identify_rotated_lines()` and `map_line_directions()` both call `get_text("dict")`. They're currently only called from geometry paths excluded from OCR runs — but the proxy's incomplete contract is a real latent bug if the supported check set expands. |
| DA: 0.36pt stroke filter bypassed by ISO lineweights | **CONFIRMED** | ISO standard text layer pen widths are 0.25mm (≈0.71pt) — twice the threshold. Any drawing using ISO lineweights on the text layer would saturate the circuit-breaker instead of hitting the per-word filter. |
| DA: `get_textpage_ocr()` exists since PyMuPDF 1.21 | **CONFIRMED** | The entire subprocess + temp PNG + TSV parse + coordinate scaling + OCRPageProxy pipeline is what `get_textpage_ocr()` already does natively. Significant simplification opportunity. |
| DA: Spelling 100% skipped on PDFSHX=1 = tool's primary function fails on common input | **CONFIRMED** | Cannot be dismissed as a minor limitation. AutoCAD SHX is the most common legacy drawing text format. The tool's name is SpellCheckPDF_Word.py. |
| DA: 300 DPI marginal for 2mm CAD text | **CONFIRMED** | 2mm text at 300 DPI ≈ 24px character height. Tesseract LSTM reliable minimum is ~30px. 400 DPI ≈ 31px — crosses the threshold. This is a real, calculable problem. |

---

## B. Priority Ranking

| # | Issue | Severity | Fixable now | Effort |
|---|---|---|---|---|
| 1 | No `--psm 11 --oem 1` flags on Tesseract call | **High** | Yes | Small |
| 2 | `OCR_DPI = 300` too low for small CAD text | **High** | Yes | Small |
| 3 | `OCR_MIN_CONFIDENCE = 40` wrong in both directions | **Medium** | Yes | Small |
| 4 | Blank-page guard missing — OCR fires on cover sheets | **Medium** | Yes | Small |
| 5 | OCRPageProxy `get_text("dict")` unpatched | **Medium** | Yes | Small |
| 6 | 0.36pt stroke-width filter bypassed by ISO lineweights | **Medium** | Yes | Small |
| 7 | Spelling 100% absent on PDFSHX=1 | **High** | Partially | Large |
| 8 | Migrate to `get_textpage_ocr()` | **Low** | Yes | Medium |

---

## C. Fix Proposal — Copy-Paste-Ready Code Changes

### Fix 1: Tesseract Flags — `SpellCheckOCR_Fallback.py`

**Problem**: PSM 3 mis-segments isolated CAD title block fields. OEM 3 adds legacy engine noise. Project codes penalised without explicit flags.

**File**: `SpellCheckOCR_Fallback.py`, function `run_tesseract_tsv()`

OLD (line ~117):
```python
    result = subprocess.run(
        [tesseract_exe, image_path, output_base, "tsv"],
        capture_output=True, text=True, timeout=120,
    )
```

NEW:
```python
    result = subprocess.run(
        [
            tesseract_exe, image_path, output_base,
            "--psm", "11",   # sparse text: find text anywhere without assuming layout structure.
                             # Correct for CAD title blocks where fields are isolated and widely
                             # spaced — PSM 3 (default) expects column layout and mis-segments these.
            "--oem", "1",    # LSTM engine only: faster and more accurate on clean rasterised images
                             # than OEM 3 (legacy+LSTM combined). No legacy engine benefit here.
            "tsv",
        ],
        capture_output=True, text=True, timeout=120,
    )
```

---

### Fix 2: DPI Increase — `SpellCheckOCR_Fallback.py`

**Problem**: 2mm text ≈ 24px at 300 DPI. Tesseract LSTM reliable minimum is ~30px. 400 DPI brings 2mm text to ~31px.

**File**: `SpellCheckOCR_Fallback.py`, line ~63

OLD:
```python
OCR_DPI = 300  # render resolution - higher helps accuracy, costs time
```

NEW:
```python
OCR_DPI = 400  # render resolution for CAD PDFs. 300 DPI renders 2mm title-block text at ~24px
               # character height — right at Tesseract LSTM's reliable-recognition floor (~30px).
               # 400 DPI brings 2mm text to ~31px, materially improving accuracy on the exact
               # content the OCR checks target (title block fields, BOM cells, REV letters).
               # Cost: render time increases ~78% (area scales as DPI²) — acceptable for the
               # small number of SHX pages that reach this path.
```

---

### Fix 3: Confidence Threshold Split — `SpellCheckOCR_Fallback.py`

**Problem**: `OCR_MIN_CONFIDENCE = 40` is too low for standard text (accepts genuinely ambiguous reads) and too high for project codes (silently drops correctly-read alphanumeric identifiers).

**File**: `SpellCheckOCR_Fallback.py`, lines ~63–64

OLD:
```python
OCR_DPI = 400
OCR_MIN_CONFIDENCE = 40  # Tesseract's own 0-100 confidence score per word
```

NEW:
```python
OCR_DPI = 400
OCR_MIN_CONFIDENCE = 50        # Tesseract's own 0-100 confidence score per word (standard text:
                                # dates, names, descriptions, REV letters). Raised from 40: score
                                # of 40-49 on readable text indicates genuine ambiguity.
OCR_MIN_CONFIDENCE_CODES = 30  # Lower threshold for alphanumeric codes (project numbers like
                                # PJ00193, drawing numbers like AB-1234-001). Tesseract's English
                                # language model penalises non-dictionary tokens — a correctly-read
                                # project code often scores 30-45, below the standard threshold.
                                # Applied selectively before project-number and item-reference checks.
```

In `run_ocr_fallback_checks()`, generate two word sets — one at standard confidence for BOM/REV checks, one at code confidence for project-number and item-reference checks:

```python
    # Standard word set — BOM, REV, title-block checks
    ocr_words, diagnostic = ocr_extract_words(real_page, tesseract_exe)
    if not ocr_words:
        return False, diagnostic

    # Lower-confidence word set — for checks matching alphanumeric codes
    # (project numbers, drawing references) that Tesseract's English LM penalises.
    # We re-parse the same TSV rows at the lower threshold rather than re-running OCR.
    # NOTE: requires refactoring ocr_extract_words() to expose the raw TSV rows.
    # For now: run OCR twice (acceptable given this path already does a full render).
    ocr_words_codes, _ = ocr_extract_words(real_page, tesseract_exe,
                                           min_confidence=OCR_MIN_CONFIDENCE_CODES)
```

The `ocr_extract_words` signature already accepts `min_confidence` implicitly via `OCR_MIN_CONFIDENCE` — add it as an explicit parameter for caller override.

---

### Fix 4: Blank-Page Guard — `SpellCheckPDF_Word.py`

**Problem**: Zero-text trigger fires on blank cover sheets and logo-only pages, producing garbage OCR results or unexplained empty reports.

**Location**: `SpellCheckPDF_Word.py`, in the per-page processing loop, immediately before the OCR fallback call.

```python
# --- Blank-page guard before OCR fallback ---
# A zero-text page is a SHX-font page (needs OCR) OR an intentionally sparse page
# (blank continuation sheet, cover sheet with only a logo image, border-only page).
# These look identical from text extraction alone. Distinguishing heuristic:
# SHX pages have extensive drawing geometry (vector glyph strokes + drawing content).
# A genuinely blank or logo-only page has very few or no drawing segments.
#
# Threshold: if the page has fewer than OCR_BLANK_PAGE_MIN_SEGMENTS drawing segments,
# treat it as intentionally sparse — skip OCR and report as blank, not SHX.
# Calibrate: a minimal border-only page typically has ~4-12 segments (rectangle edges).
# A real SHX drawing page typically has 200+ (glyph strokes alone for a few words of
# SHX text generate 30-50 segments each). 50 is a conservative floor.
OCR_BLANK_PAGE_MIN_SEGMENTS = 50  # define at module level with other constants

if len(words) == 0:
    drawings = page.get_drawings()
    total_segments = sum(len(d.get("items", [])) for d in drawings)
    if total_segments < OCR_BLANK_PAGE_MIN_SEGMENTS:
        # Intentionally sparse page — not SHX. Skip OCR.
        ensure_page_header()
        report_lines.append(
            f"  Page {page_num + 1}: no extractable text and minimal drawing geometry "
            f"({total_segments} segment(s) < {OCR_BLANK_PAGE_MIN_SEGMENTS} threshold) — "
            f"treated as intentionally blank/sparse, not an SHX-font page. OCR skipped."
        )
        continue  # skip to next page
    # else: fall through to OCR fallback
```

---

### Fix 5: OCRPageProxy `get_text("dict")` Patch — `SpellCheckOCR_Fallback.py`

**Problem**: Proxy incomplete — `get_text("dict")` passes to real (empty) page. Latent bug for any future check using dict path.

**File**: `SpellCheckOCR_Fallback.py`, `OCRPageProxy` class

OLD:
```python
class OCRPageProxy:
    def __init__(self, real_page, ocr_words):
        self._real_page = real_page
        self._ocr_words = ocr_words

    def get_text(self, kind="text"):
        if kind == "words":
            return self._ocr_words
        return self._real_page.get_text(kind)

    def __getattr__(self, name):
        return getattr(self._real_page, name)
```

NEW:
```python
class OCRPageProxy:
    """Wraps a real fitz page, returning OCR-derived words for get_text("words") and a
    synthetic dict structure for get_text("dict"). Everything else passes to the real page.

    get_text("dict") is patched because identify_rotated_lines() and map_line_directions()
    use it to read text direction vectors — on a zero-text SHX page the real page returns
    empty blocks, so any check calling those helpers would silently get no rotation data.
    The synthetic dict wraps OCR words as a single horizontal text block (dir=(1,0)) since
    OCR-derived words have no reliable rotation information — this is correct for title-block
    content, which is always horizontal.
    """

    def __init__(self, real_page, ocr_words):
        self._real_page = real_page
        self._ocr_words = ocr_words

    def get_text(self, kind="text"):
        if kind == "words":
            return self._ocr_words
        if kind == "dict":
            return self._synthetic_dict()
        return self._real_page.get_text(kind)

    def _synthetic_dict(self):
        """Returns a minimal get_text("dict")-compatible structure wrapping OCR words.
        Each OCR word becomes a span in a single line in a single block.
        dir=(1,0) for all lines — OCR words have no rotation information; title-block
        content is always horizontal so this is correct for the OCR-supported check set."""
        if not self._ocr_words:
            return {"blocks": []}
        spans = []
        for (x0, y0, x1, y1, text, block_no, line_no, word_no) in self._ocr_words:
            spans.append({
                "text": text,
                "bbox": (x0, y0, x1, y1),
                "font": "OCR",
                "size": (y1 - y0),
                "flags": 0,
                "color": 0,
                "origin": (x0, y1),
            })
        page_rect = self._real_page.rect
        return {
            "blocks": [{
                "type": 0,
                "number": 0,
                "bbox": (page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1),
                "lines": [{
                    "dir": (1.0, 0.0),
                    "bbox": (page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1),
                    "spans": spans,
                }],
            }],
        }

    def __getattr__(self, name):
        return getattr(self._real_page, name)
```

---

### Fix 6: SHX Stroke-Width Threshold + Circuit-Breaker Reporting — `SpellCheckPDF_Word.py`

**Problem**: 0.36pt threshold calibrated on one AutoCAD config. ISO 0.25mm text layer (≈0.71pt) bypasses filter. Circuit-breaker suppression is silent.

**Part A** — raise threshold to 0.50pt to cover ISO 0.13mm text layer assignments:

```python
# OLD:
# stroke width ≤ 0.36pt — own SHX character stroke
if width <= 0.36 and both_endpoints_inside:
    continue

# NEW:
SHX_GLYPH_MAX_STROKE_PT = 0.50  # define at module level with other constants
# Raised from 0.36pt to 0.50pt to cover ISO 0.13mm text layer (≈0.37pt) and
# similar lightweight pen assignments. ISO 0.25mm (≈0.71pt) still bypasses —
# circuit-breaker handles page-wide saturation in that case.
if width <= SHX_GLYPH_MAX_STROKE_PT and both_endpoints_inside:
    continue
```

**Part B** — add a report line when the circuit-breaker fires:

```python
# Where GEOMETRY_SANITY_MAX_FRACTION / GEOMETRY_SANITY_MIN_ABSOLUTE threshold is met:
report_lines.append(
    f"  Page {page_num + 1}: geometry checks SUPPRESSED — {n_crossing_flags} crossing "
    f"flags on {n_words} words ({fraction:.1%}) exceeds sanity threshold "
    f"({GEOMETRY_SANITY_MAX_FRACTION:.0%} of words, min {GEOMETRY_SANITY_MIN_ABSOLUTE}). "
    f"Likely SHX-font page with vector glyph outlines — line-crossing flags suppressed "
    f"to avoid noise."
)
```

---

### Fix 7 (Migration Note Only): `get_textpage_ocr()` Path

**Not a code change for this patch — tracked as the next architectural step after fixes 1–6 are validated in production.**

PyMuPDF ≥ 1.21.0 provides `page.get_textpage_ocr(dpi=400, full=True, language="eng")` which internally renders, calls Tesseract via C bindings, and returns a `TextPage` with word-level coordinates already in PDF space.

Key 5-line replacement for the entire `ocr_extract_words()` pipeline:
```python
def ocr_extract_words_native(page, dpi=400):
    """Requires PyMuPDF ≥ 1.21.0 AND Tesseract on PATH or TESSDATA_PREFIX configured."""
    try:
        tp = page.get_textpage_ocr(dpi=dpi, full=True, language="eng")
        words = page.get_text("words", textpage=tp)
        if not words:
            return [], "get_textpage_ocr() returned no words"
        return words, None
    except Exception as e:
        return [], f"get_textpage_ocr() failed: {e}"
```

**What gets eliminated on migration**: `render_page_to_image()`, `run_tesseract_tsv()`, `tsv_rows_to_word_tuples()`, `find_tesseract_exe()`, `describe_tesseract_search()`, `TesseractPath.txt` search, all temp file handling, `OCRPageProxy` (real page handles `get_text("words", textpage=tp)` directly).

**Prerequisite**: Confirm `fitz.__version__ >= "1.21.0"` on all deployment machines. PSM/OEM passed as combined integer `flags` parameter — less ergonomic but documented. Confidence scores in returned word tuples vary by PyMuPDF version; verify before migrating the confidence filter.

---

## D. What NOT to Fix Now

**1. Enabling OCR spell-checking on PDFSHX=1 pages.** The gap is real and significant, but adding OCR-based spell-checking requires calibrating false positive rates on real SHX drawings after Fix 1+2 improve base accuracy. Do after fixes 1–6 are validated and accuracy data from production SHX pages is available.

**2. Full `get_textpage_ocr()` migration.** Fix 1 (PSM/OEM flags) and Fix 2 (DPI) get most of the accuracy benefit with zero risk. Migrate the architecture after those fixes are confirmed working in production.

**3. Per-drawing PSM auto-detection.** Automatically choosing PSM based on content analysis is appealing but complex and brittle. PSM 11 is the correct single mode for this use case — it degrades gracefully on all CAD layout types.

**4. `tessedit_char_whitelist`.** Limiting Tesseract to ASCII printable would reduce false positives from symbol misreads but risks dropping legitimate Unicode characters (degree signs, diameter symbols). Risk outweighs benefit at this stage.

---

## E. Confidence Table

| Fix | Confidence fixes stated problem | Regression risk |
|---|---|---|
| Fix 1: `--psm 11 --oem 1` Tesseract flags | **High** — PSM 11 specifically documented for sparse text layouts; directly addresses mis-segmentation | **Low** — only OCR word extraction affected; no check logic changes |
| Fix 2: `OCR_DPI = 400` | **High** — pixel height calculation is deterministic; 400 DPI crosses Tesseract's reliable floor for 2mm text | **Low** — slower render, no logic changes |
| Fix 3: Split confidence thresholds (50 standard / 30 codes) | **Medium** — addresses the penalisation mechanism correctly; threshold values need validation on real SHX drawings | **Medium** — lowering threshold for codes may increase false-positive OCR reads; needs a test pass |
| Fix 4: Blank-page guard (50-segment threshold) | **Medium** — SHX vs blank distinction is real; segment count threshold needs calibration against real blank cover sheets | **Low** — only skips OCR on very sparse pages; false negatives require the drawing to have almost no geometry |
| Fix 5: OCRPageProxy `get_text("dict")` patch | **High** — eliminates the latent bug definitively; synthetic dict correct for horizontal title-block content | **Low** — only affects OCR proxy path; real page dict still used for non-OCR pages |
| Fix 6: SHX stroke threshold 0.36→0.50pt + circuit-breaker reporting | **Medium** — covers more ISO pen widths; reporting improvement is High confidence | **Low** — raising threshold slightly increases per-word filter catches; reporting change is additive only |

---

## Summary

The architecture is sound in its two-path split and graceful degradation. The implementation has four concrete, fixable bugs actively suppressing real findings: no Tesseract PSM/OEM flags, insufficient DPI, incomplete OCRPageProxy, and no blank-page guard.

**Fix 1 + Fix 2** together will materially improve OCR accuracy on the specific content the fallback was built for (title block fields, BOM cells, REV letters). These are the highest-impact changes with the lowest regression risk — implement immediately.

**Fix 4** closes a latent bug before it bites. **Fix 5** stops false "OCR found text" reports on blank cover sheets. **Fix 3** and **Fix 6** require calibration against real drawings before committing to specific thresholds.

The `get_textpage_ocr()` migration is the right long-term path — architectural simplification that eliminates the subprocess pipeline — but not a current correctness fix.

Spelling on PDFSHX=1 pages remains 100% absent and is the correct next feature to build after OCR accuracy is confirmed with Fix 1+2 in production.

*SSA output — SpellCheck SHX audit MAD cycle*
