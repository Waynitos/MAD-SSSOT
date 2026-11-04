"""
SpellCheckOCR_Fallback.py
==========================
OCR-based fallback for PDFs that have zero extractable text - e.g. AutoCAD
drawings exported with SHX-font text flattened to vector outlines, where
there is no real text object anywhere on the page for direct extraction to
find.

Used AUTOMATICALLY by SpellCheckPDF_Word.py - only when a page's normal
text extraction comes back completely empty. Files with real text (the
vast majority - all Inventor exports, and any AutoCAD export using
TrueType text or PDFSHX=2) never touch this module at all.

WHY A SEPARATE MODULE:
Rendering a page to an image and reading pixels is a fundamentally
different, less accurate approach than direct text extraction - dense,
small CAD text (dimensions, symbols, notes) is exactly what OCR struggles
with. Keeping this in its own file means a Tesseract problem on some
machine can only ever affect the already-flagged zero-text files, never
the normal high-confidence extraction path everything else uses.

WHAT IT CHECKS:
Only the checks that read large, well-spaced text where OCR is reliable:
BOM sequence, project number, REV comparison (corner vs table), REV
description, and the old-title-block-version check. Spelling and the
geometry-dependent checks (line crossing, text overlap, balloon overlap)
are skipped entirely on OCR'd pages - OCR mistakes on small dense text
would create more noise than signal for those.

REQUIRES a working Tesseract-OCR install. Looked for in this order:
    1. Tesseract-OCR/tesseract.exe next to this script (shared server copy)
    2. Common local user-install locations (AppData\\Local etc.)
If not found, the caller falls back to the existing "no extractable text -
SKIPPED" result exactly as before - this module never hard-fails the tool.
"""

import os
import re
import csv
import subprocess
import tempfile
from pathlib import Path

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Explicit override - if this file exists, its contents (a single line,
# the full path to tesseract.exe) are used FIRST, before any automatic
# search. This removes all guesswork about environment variables/user
# profiles differing between machines or execution contexts - just paste
# the real path in this file and it's guaranteed to be used.
TESSERACT_PATH_OVERRIDE_FILE = os.path.join(_THIS_DIR, "TesseractPath.txt")

# Where to look for tesseract.exe if no override file is present, in
# priority order. The shared server copy (deployed once, used by everyone
# - no per-machine install needed) is checked first.
_TESSERACT_SEARCH_PATHS = [
    os.path.join(_THIS_DIR, "Tesseract-OCR", "tesseract.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
    os.path.join(os.environ.get("PROGRAMFILES", ""), "Tesseract-OCR", "tesseract.exe"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Tesseract-OCR", "tesseract.exe"),
]

OCR_DPI = 400  # render resolution for CAD PDFs. 300 DPI renders 2mm title-block text at ~24px
               # character height — right at Tesseract LSTM's reliable-recognition floor (~30px).
               # 400 DPI brings 2mm text to ~31px, materially improving accuracy on the exact
               # content the OCR checks target (title block fields, BOM cells, REV letters).
               # Cost: render time increases ~78% (area scales as DPI²) — acceptable for the
               # small number of SHX pages that reach this path.
OCR_MIN_CONFIDENCE = 50        # Tesseract's own 0-100 confidence score per word (standard text:
                                # dates, names, descriptions, REV letters). Raised from 40: score
                                # of 40-49 on readable text indicates genuine ambiguity.
OCR_MIN_CONFIDENCE_CODES = 30  # Lower threshold for alphanumeric codes (project numbers like
                                # PJ00193, drawing numbers like AB-1234-001). Tesseract's English
                                # language model penalises non-dictionary tokens — a correctly-read
                                # project code often scores 30-45, below the standard threshold.
                                # Applied selectively before project-number and item-reference checks.


def find_tesseract_exe():
    """Returns the path to tesseract.exe if found, else None. Never raises.
    Checks the explicit override file first, then falls back to the
    automatic search paths."""
    if os.path.exists(TESSERACT_PATH_OVERRIDE_FILE):
        try:
            with open(TESSERACT_PATH_OVERRIDE_FILE, "r", encoding="utf-8") as f:
                override_path = f.read().strip().strip('"')
            if override_path and os.path.exists(override_path):
                return override_path
        except Exception:
            pass
    for candidate in _TESSERACT_SEARCH_PATHS:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def describe_tesseract_search():
    """Human-readable list of every location that was checked - used to
    build an actionable message when tesseract.exe can't be found at all,
    so troubleshooting doesn't need another round-trip."""
    lines = [f"  Override file (checked first): {TESSERACT_PATH_OVERRIDE_FILE}"]
    if os.path.exists(TESSERACT_PATH_OVERRIDE_FILE):
        lines[-1] += "  [EXISTS but path inside it wasn't found]"
    else:
        lines[-1] += "  [not present]"
    for p in _TESSERACT_SEARCH_PATHS:
        lines.append(f"  {p}")
    return "\n".join(lines)


def render_page_to_image(page, tmp_dir, dpi=OCR_DPI):
    """Renders a fitz page to a PNG file. Returns (image_path, scale) where
    scale converts pixel coordinates back to PDF point coordinates
    (pdf_point = pixel / scale)."""
    import fitz
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=matrix)
    image_path = os.path.join(tmp_dir, "ocr_page.png")
    pix.save(image_path)
    return image_path, scale


def run_tesseract_tsv(image_path, tesseract_exe, tmp_dir):
    """Runs tesseract on an image, returns the parsed TSV rows as a list of
    dicts (Tesseract's own --tsv output format: level, page_num, block_num,
    par_num, line_num, word_num, left, top, width, height, conf, text)."""
    output_base = os.path.join(tmp_dir, "ocr_output")
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
    if result.returncode != 0:
        raise RuntimeError(f"Tesseract failed: {result.stderr.strip()}")

    tsv_path = output_base + ".tsv"
    rows = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            rows.append(row)
    return rows


def tsv_rows_to_word_tuples(rows, scale, min_confidence=OCR_MIN_CONFIDENCE):
    """Converts Tesseract TSV rows into the SAME word-tuple format PyMuPDF's
    page.get_text("words") returns: (x0, y0, x1, y1, text, block_no,
    line_no, word_no). This is the key integration point - every existing
    check function that reads this tuple format works unmodified on
    OCR-derived words, no separate OCR-aware logic needed per check."""
    words = []
    for row in rows:
        try:
            level = int(row["level"])
        except (KeyError, ValueError):
            continue
        if level != 5:  # level 5 = word level in Tesseract's TSV hierarchy
            continue
        text = (row.get("text") or "").strip()
        if not text:
            continue
        try:
            conf = float(row["conf"])
        except (KeyError, ValueError):
            conf = -1
        if conf < min_confidence:
            continue
        try:
            left = float(row["left"]) / scale
            top = float(row["top"]) / scale
            width = float(row["width"]) / scale
            height = float(row["height"]) / scale
        except (KeyError, ValueError):
            continue
        block_no = int(row.get("block_num", 0) or 0)
        line_no = int(row.get("line_num", 0) or 0)
        word_no = int(row.get("word_num", 0) or 0)
        words.append((left, top, left + width, top + height, text, block_no, line_no, word_no))
    return words


def ocr_extract_words(page, tesseract_exe, dpi=OCR_DPI, min_confidence=OCR_MIN_CONFIDENCE):
    """Full pipeline: render page -> run tesseract -> parse into word
    tuples. Returns (words, diagnostic) - words is [] on any failure, and
    diagnostic explains exactly WHERE and why, rather than silently
    swallowing every possible failure into an indistinguishable empty
    result. Never raises, so a single problem file never crashes the
    whole batch.

    min_confidence: override for Tesseract confidence threshold. Use
    OCR_MIN_CONFIDENCE_CODES when extracting words for project-number or
    item-reference checks — these alphanumeric codes are penalised by the
    English language model and score below OCR_MIN_CONFIDENCE even when
    correctly read."""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                image_path, scale = render_page_to_image(page, tmp_dir, dpi=dpi)
            except Exception as e:
                return [], f"failed to render page to an image: {e}"

            try:
                rows = run_tesseract_tsv(image_path, tesseract_exe, tmp_dir)
            except Exception as e:
                return [], f"tesseract subprocess failed: {e}"

            if not rows:
                return [], "tesseract produced no output rows at all (empty TSV)"

            all_words_any_confidence = tsv_rows_to_word_tuples(rows, scale, min_confidence=-1)
            words = tsv_rows_to_word_tuples(rows, scale, min_confidence=min_confidence)
            if not words:
                if all_words_any_confidence:
                    return [], (
                        f"tesseract read {len(all_words_any_confidence)} word(s) but none met "
                        f"the confidence threshold (>={min_confidence}) - image may be too "
                        f"low quality/resolution for reliable OCR at this content"
                    )
                return [], "tesseract found no words at any confidence level (page may be genuinely blank, or rendering failed silently)"

            return words, None
    except Exception as e:
        return [], f"unexpected error in OCR pipeline: {e}"


class OCRPageProxy:
    """Wraps a real fitz page, returning OCR-derived words for get_text("words") and a
    synthetic dict structure for get_text("dict"). Everything else - insert_text,
    new_shape, search_for, rect, get_drawings - passes to the real page unchanged.

    get_text("dict") is patched because identify_rotated_lines() and map_line_directions()
    use it to read text direction vectors — on a zero-text SHX page the real page returns
    empty blocks, so any check calling those helpers would silently get no rotation data.
    The synthetic dict wraps OCR words as a single horizontal text block (dir=(1,0)) since
    OCR-derived words have no reliable rotation information — this is correct for title-block
    content, which is always horizontal.

    CONTRACT: get_text("words") and get_text("dict") are intercepted with OCR data.
    All other get_text() variants and all other fitz page attributes pass through to the
    real page. For zero-text SHX pages, get_text("text"), get_text("html") etc. will
    return empty/minimal results from the real page — this is expected and correct.
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
                    "dir": (1.0, 0.0),   # horizontal — OCR has no rotation data
                    "bbox": (page_rect.x0, page_rect.y0, page_rect.x1, page_rect.y1),
                    "spans": spans,
                }],
            }],
        }

    def __getattr__(self, name):
        return getattr(self._real_page, name)


# The checks OCR text is reliable enough for: large, well-spaced text
# (title block fields, BOM table cells, REV letters/numbers). Spelling and
# the geometry-dependent checks (line crossing, text overlap, balloon
# overlap) are deliberately excluded - OCR mistakes on small, dense CAD
# text (dimensions, symbols, notes) would create more false positives than
# genuine defects caught.
OCR_SUPPORTED_CHECK_KEYS = [
    "bom_out_of_seq", "bom_missing", "project_number",
    "rev_stamp_wrong", "rev_stamp_missing", "rev_stamp_conflict",
    "rev_compare_mismatch", "rev_description_mismatch",
    "item_reference_length", "item_upstream_mismatch",
    "titleblock_old_version",
]


def run_ocr_fallback_checks(main_module, real_page, page_num, reference_project_number,
                             report_lines, counts, ensure_page_header, tesseract_exe):
    """Orchestrates the OCR fallback for one page with zero extractable
    text: OCR the page, wrap it in a proxy, and run the subset of checks
    that are reliable on OCR'd text - reusing the SAME check functions
    SpellCheckPDF_Word.py already uses for direct text extraction, just
    fed OCR-derived words instead. Returns (used_ocr, diagnostic) -
    used_ocr is True if OCR produced any usable text at all (even if
    every check passed clean); diagnostic explains why OCR came back
    empty when used_ocr is False, so a truly blank page and a broken OCR
    pipeline don't look identical in the report.

    Two confidence thresholds are used:
    - OCR_MIN_CONFIDENCE (50): for standard English text (REV descriptions,
      BOM descriptions, title block text). Higher threshold rejects genuinely
      ambiguous reads.
    - OCR_MIN_CONFIDENCE_CODES (30): for alphanumeric code checks (project number,
      item references). Tesseract's English language model penalises non-dictionary
      tokens like PJ00193, depressing their confidence below the standard threshold
      even when correctly read. Lower threshold prevents silently dropping valid codes.
    """
    ocr_words, diagnostic = ocr_extract_words(real_page, tesseract_exe)
    if not ocr_words:
        return False, diagnostic

    # Separate lower-confidence word set for project/item code checks.
    # These run a second extraction pass at OCR_MIN_CONFIDENCE_CODES.
    # The page is already rendered in the call above — re-running is acceptable
    # given the small number of SHX pages that reach this path.
    ocr_words_codes, _ = ocr_extract_words(
        real_page, tesseract_exe, min_confidence=OCR_MIN_CONFIDENCE_CODES
    )

    report_lines.append(
        f"  Page {page_num + 1}: no extractable text found directly - used OCR fallback "
        f"({len(ocr_words)} word(s) read at confidence>={OCR_MIN_CONFIDENCE}; "
        f"{len(ocr_words_codes)} word(s) at code threshold>={OCR_MIN_CONFIDENCE_CODES}). "
        f"NOTE: OCR is less accurate than direct text extraction - only BOM/REV/project-"
        f"number/title-block checks ran; spelling and line-crossing/overlap checks were "
        f"skipped for this page."
    )

    # Standard proxy (higher confidence threshold) for text-content checks
    page = OCRPageProxy(real_page, ocr_words)
    # Code proxy (lower confidence threshold) for alphanumeric identifier checks
    page_codes = OCRPageProxy(real_page, ocr_words_codes if ocr_words_codes else ocr_words)

    main_module.run_bom_sequence_check(page, page_num, report_lines, counts, ensure_page_header)
    # Project number and item reference checks use lower-confidence word set — alphanumeric
    # codes like PJ00193 are penalised by Tesseract's English language model.
    main_module.run_project_number_check(page_codes, page_num, reference_project_number, report_lines, counts, ensure_page_header)
    main_module.run_revision_stamp_check(page, page_num, report_lines, counts, ensure_page_header)
    main_module.run_rev_compare_check(page, page_num, report_lines, counts, ensure_page_header)
    main_module.run_rev_description_check(page, page_num, report_lines, counts, ensure_page_header)
    main_module.run_item_reference_check(page_codes, page_num, report_lines, counts, ensure_page_header)
    main_module.run_item_upstream_reference_check(page_codes, page_num, report_lines, counts, ensure_page_header)
    main_module.run_titleblock_version_check(page, page_num, report_lines, counts, ensure_page_header)

    return True, None


# =============================================================================
# FUTURE MIGRATION NOTE: get_textpage_ocr() — PyMuPDF native OCR
# =============================================================================
# PyMuPDF ≥ 1.21.0 (released November 2022) provides page.get_textpage_ocr()
# which internally renders to a pixmap, calls Tesseract via C bindings (no
# subprocess), and returns a TextPage with word-level coordinates in PDF space.
#
# The 5-line replacement for the entire subprocess pipeline above:
#
#   def ocr_extract_words_native(page, dpi=OCR_DPI):
#       """Requires PyMuPDF >= 1.21.0 AND Tesseract on PATH or TESSDATA_PREFIX."""
#       try:
#           tp = page.get_textpage_ocr(dpi=dpi, full=True, language="eng")
#           words = page.get_text("words", textpage=tp)
#           return (words, None) if words else ([], "get_textpage_ocr() returned no words")
#       except Exception as e:
#           return [], f"get_textpage_ocr() failed: {e}"
#
# What gets eliminated on migration: render_page_to_image(), run_tesseract_tsv(),
# tsv_rows_to_word_tuples(), find_tesseract_exe(), describe_tesseract_search(),
# TesseractPath.txt search, all temp file handling, OCRPageProxy (real page handles
# get_text("words", textpage=tp) directly — no proxy needed).
#
# Prerequisites:
# - Confirm fitz.__version__ >= "1.21.0" on all deployment machines
# - PSM/OEM passed as combined integer 'flags' parameter (less ergonomic, documented)
# - Verify confidence scores in returned word tuples before migrating confidence filter
#
# Migrate after fixes 1-6 above are validated in production on real SHX drawings.
# =============================================================================
