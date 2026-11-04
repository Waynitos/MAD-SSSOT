"""
SpellCheckPDF_Word.py
=====================
Inventor Drawing PDF Checker - Spelling + Drawing Consistency Checks

VERSION : 2026-10-23-merged-v15ab
UPDATED : 2026-10-20
CHANGES : - Performance: page.get_drawings() now called once per page (shared
            between line-crossing and balloon segment indexes)
          - Performance: page.get_text("words") now called once per page
            (shared between spelling, geometry, and project-number checks)
          - Performance: DEBUG_MODE set to False (no per-candidate debug dumps)
          - New check: drawing number in title block must be contained in the
            PDF filename (flags if title block number doesn't match filename)
          - Fix: drawing number check now requires the "DRAWING NUMBER" label
            to anchor the column - prevents drawing references in notes text
            from being mistaken for the title block number
          - Fix (v15n): requires both DRAWING+NUMBER tokens on same row;
            uses tight Y-band (±1.5 row-heights) around label to exclude
            notes-text drawing references on large A1/A0 sheets
          - Fix (v15o): also handle "DRAWING NUMBER" as a single combined
            token (common in many PDF exports); widen Y-band to ±3 row-heights
            to reliably catch the value cell beneath the label header
          - Fix (v15p): replaced label-anchor approach entirely; now uses
            bottommost-wins: title block number is always the lowest hyphenated
            token with the right prefix in the corner — no label search needed
          - New (v15q): project number mismatch highlights now show the correct
            project number in red text below the highlight
          - New (v15q): drawing number mismatch highlights now show the correct
            drawing number (filename stem, underscore suffix stripped) in red
            text below the highlight

BUILD MARKER: 2026-10-22-merged-v15q
  If the report a run of this script produces doesn't show this marker
  anywhere obvious to cross-check, or behaves inconsistently with what's
  described in chat, the file being run may not be the latest version -
  worth re-downloading and re-testing before treating any given behavior
  as a new bug. (Search for BUILD_MARKER below - it's also written into
  the top of every report this script generates.)

Combines everything into one pass over each PDF:
    1. SPELLING - direct text extraction spell-check (not OCR)
    2. N/A MASS REFERENCE - flags where Inventor's mass reference field
       hasn't updated
    3. LINE CROSSING - text/balloon numbers cut through by a drawing line
    4. TEXT OVERLAP - leftover placeholder text stacked under real text
    5. BALLOON OVERLAP - two balloon circles physically overlapping
    6. BOM SEQUENCE - item numbers out of order or missing from the
       sequence entirely
    7. PROJECT NUMBER - project-code tokens elsewhere on the drawing that
       don't match the correct one taken from the PDF's own filename
    8. REVISION STAMP - REV letter/number vs PRELIMINARY/APPROVED stamp
       consistency
    9. REV COMPARE - main title block REV vs revisions-table REV
    10. REV DESCRIPTION - revisions-table DESCRIPTION vs corner REV
    11. ITEM REFERENCE LENGTH - detail-view ITEM reference numbers must be
        6 digits
    12. ITEM UPSTREAM REFERENCE - ITEM reference number's last 3 digits
        must match an up-stream-referenced drawing number

All flags use the same red highlight. Works best with text-based PDFs
(Inventor exports, most CAD PDFs) - does NOT work with scanned/image-based
PDFs.

HOW TO RUN:
    Double-click SpellCheck.bat
    OR:
        python SpellCheckPDF_Word.py

OUTPUT:
    <original_name>_SpellCheck.pdf  saved beside the source file, in a
    SPELLCHECK DWGS subfolder. Only created if any issue is found.
"""

import sys
import subprocess

def install_missing():
    import importlib
    packages = {
        "PyMuPDF":        "fitz",
        "pyspellchecker": "spellchecker",
        "Pillow":         "PIL",
    }
    for pkg, imp in packages.items():
        try:
            importlib.import_module(imp)
        except ImportError:
            print(f"  Installing {pkg} ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

print("Checking dependencies...")
install_missing()
print("All dependencies ready.")

import os
import re
import math
import traceback
import ctypes
import ctypes.wintypes as wintypes
import shutil
import tempfile
from pathlib import Path
import fitz  # pymupdf - used for text extraction AND drawing highlights
from spellchecker import SpellChecker

# Explicitly add this script's own directory to sys.path before importing
# any sibling module. Normally Python does this automatically when you run
# `python script.py` - but confirmed on a real machine running this from a
# portable/embeddable Python distribution (a "python" folder bundled next
# to the script rather than a full system install): those ship with a
# restrictive pythonXY._pth file that can lock sys.path down to just the
# interpreter's own bundled zip/DLLs, silently leaving the script's own
# folder off it. The practical symptom was SpellCheckOCR_Fallback.py
# sitting in the exact right place, correctly named, and still raising
# ModuleNotFoundError - confirmed even with `python -c "import ..."` run
# from that exact directory. Doing this explicitly here works regardless
# of how the interpreter itself is configured, rather than depending on
# every deployment's Python setup behaving the same way.
_SCRIPT_DIR_EARLY = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR_EARLY not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR_EARLY)

# OCR fallback - only used for pages with zero extractable text (e.g.
# AutoCAD SHX-font exports flattened to vector outlines). Imported
# gracefully: a missing file or missing Tesseract install just means those
# pages get the existing "no extractable text - SKIPPED" result exactly as
# before, never a hard crash for the whole batch.
#
# The reason for a failed import is captured (not just swallowed) so a
# silent "OCR never even loaded" doesn't get reported identically to
# "OCR loaded fine but genuinely found nothing" - those are very
# different problems to fix and previously looked the same in the report.
_ocr_import_error = None
try:
    import SpellCheckOCR_Fallback as ocr_fallback
except Exception as e:
    ocr_fallback = None
    _ocr_import_error = f"{type(e).__name__}: {e}"

# -------------------------------------------------------------------
# PATHS - automatically relative to script location
# Works from any folder including a network server share
# -------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Look for ignore file in config subfolder first, then same folder as script
_ignore_candidates = [
    os.path.join(_SCRIPT_DIR, "config", "SpellCheckIgnoreWords.txt"),
    os.path.join(_SCRIPT_DIR, "SpellCheckIgnoreWords.txt"),
]
IGNORE_FILE = next((p for p in _ignore_candidates if os.path.exists(p)), _ignore_candidates[0])
# -------------------------------------------------------------------

NA_HIGHLIGHT_COLOR = (1, 0.2, 0.2)   # same red as spelling mistakes for "N/A" mass reference flags
NA_HIGHLIGHT_ALPHA = 0.45            # opacity - matches spelling highlight

# Built-in engineering/drawing abbreviations to always ignore
CUSTOM_IGNORE = {
    # Units
    "mm", "cm", "km", "kg", "kn", "kpa", "mpa", "gpa", "nm", "um",
    "hz", "khz", "mhz", "rpm", "rps", "bar", "psi", "ksi",
    "deg", "rad", "sec", "min", "hrs", "lhs", "rhs",
    # General drawing abbreviations
    "uno", "std", "typ", "ref", "tbd", "tbc", "tba", "na", "nts",
    "nto", "nte", "sim", "sym", "crs", "ctr", "cof", "col",
    "assy", "subassy", "dwg", "drg", "dxf", "bom", "rev", "qty",
    "thk", "dia", "pcd", "mtg", "mfg", "matl", "spec",
    "proj", "horiz", "vert", "symm", "sect", "elev", "plan",
    "det", "fig", "sht", "rqd", "reqd", "max", "min",
    "nom", "approx", "equiv", "misc", "cont", "conc", "alt",
    "ident", "info", "inst", "instr",
    # Fit and tolerance
    "tol", "lim", "dev", "iso", "ansi", "asme", "astm", "din",
    "gdt", "mmc", "lmc", "rfs", "perp", "par", "circ", "cyl",
    "flat", "str",
    # Fasteners
    "thd", "tpi", "unc", "unf", "hex", "csk", "cbore",
    "soc", "fhd", "rhd", "btn", "shldr", "skt", "grd",
    # Materials
    "alum", "alu", "sst", "crmo", "hss", "pvc", "ptfe", "hdpe",
    "ldpe", "abs", "nylon",
    # Surface finish
    "grnd", "mach", "anod", "galv", "pltd", "ptd", "pwd", "znc",
    # Welding
    "wld", "faw", "smaw", "gmaw", "gtaw", "fcaw", "fil", "grv",
    "weldment", "weldments",
    # CAD file types
    "ipt", "iam", "idw", "ipn", "dwf", "igs", "stp", "step", "stl",
    # Correctly spelled words that pyspellchecker incorrectly flags
    # (frequency-based dictionary sometimes misses technical/formal words)
    "revised", "issued", "revision", "fabricator", "traceability",
    "passivation", "countersink", "counterbore", "nondestructive",
    "intermittent", "perpendicular", "procurement", "reinforcement",
    "certification", "centreline", "centerline", "subframe",
    "loadcase", "flowrate", "weldment", "ductwork", "isometric",
    "radiographic", "orthographic", "ultrasonic", "hydrostatic",
    "galvanised", "galvanized", "annealing", "tempering",
    "reaming", "chamfer", "bevel", "gusset", "datum",
    "stiffener", "deflection", "concentric", "symmetrical",
    "excavation", "ventilation", "contraction", "expansion",
    "fastening", "tapping", "turning", "milling", "drilling",
    "blasting", "coating", "rigging", "lifting", "hatching",
    "compliance", "clearance", "allowance", "tolerance",
    "alignment", "projection", "elevation", "fabrication",
    "insulation", "installation", "inspection", "dimension",
    "penetration", "corrosion", "abrasion", "oxidation",
    "vibration", "pressure", "hardness", "thickness", "radius",
    "parallel", "seismic", "bracket", "profile", "plasma",
    "vacuum", "layout", "thread", "flange", "nozzle", "anchor",
    "particle", "capacity", "assembly", "beam", "bolt", "pipe",
    "duct", "channel", "section", "angle", "cutting", "welding",
    "drawing", "surface", "machining", "grout", "shear",
    "gauge", "datum", "laser", "spool", "fillet", "plate",
    # Common PDF text split fragments - first/last chars stored as separate text objects
    "dimens", "evised", "valv", "aili",
    "escription", "onstruction", "latework",
    # Concatenated title block phrases (PDF stores these as single text objects)
    "mechanicaleng", "structuraleng", "processeng", "electricaleng",
    "civileng", "issuedforconstruction", "issuedfordesign",
    "issuedfortender", "issuedforapproval", "issuedforcomment",
    "issuedforconstructionrev", "generalarrangement",
    "lowerflotationassembly", "upperflotationassembly",
    "platformassembly", "washwaterassembly", "washwaterdistributorassembly",
    "airintakeandmanifoldassembly", "processandinstrumentdiagram",
    "donotscale", "unlessotherwisestated",
    # Title block and view labels
    "drwn", "chkd", "appd", "appr", "prep", "orig",
    "iss", "mod", "chg", "confd", "prop", "prelim",
    "section", "scale", "detail", "view", "general", "notes",
    "unless", "otherwise", "stated", "finish", "treatment",
    "revision", "history", "description", "date", "name",
    "drawing", "number", "sheet", "size", "title", "weight",
    "third", "angle", "first", "projection", "surface",
    "copyright", "rights", "reserved", "confidential",
    "checked", "approved", "drawn", "issue", "status",
}

# ==================================================================
# Drawing-check tuning knobs (line crossing, BOM, project number,
# revision stamp, rev compare, item reference checks)
# ==================================================================

BUILD_MARKER = "2026-10-28-merged-v15ai"  # bump this any time behavior changes, so
                                                       # a report can be checked against chat directly

DEBUG_MODE = False  # set True to dump balloon/overlap candidate details to the report (slow)

# ------------------------------------------------------------------
# Check enable/disable switches
# ------------------------------------------------------------------
# BALLOON-OVERLAP and CIRCLE-CROSSING are DISABLED by default.
#
# Measured on a real 30-drawing batch:
#   line crossing   :  10 flags  (0.3/drawing) - healthy, kept ON
#   text overlap    :   0 flags               - quiet, kept ON
#   balloon overlap : 152 flags  (5.1/drawing) - crying wolf, OFF
#   circle crossing : 246 flags  (8.2/drawing) - crying wolf, OFF
#
# The false positives are not borderline judgement calls, they are
# structural failures of the shape-estimation approach both checks share
# (cluster nearby segments -> guess a centre -> guess a radius -> test
# whether the guesses overlap). Confirmed failure modes from that batch:
#   - one circle fragmented into two detections, then flagged against
#     itself ("circle at (255,710) r=16 vs (254,708) r=16" - centres
#     2.8pt apart)
#   - unrelated diagonal geometry swept into a cluster and reported as a
#     97pt-radius "circle"
#   - the same balloon flagged against itself ("balloon '4' overlaps
#     balloon '4'")
#   - normal vertical balloon columns where every pair sits inside the
#     80pt proximity threshold
# No threshold separates "estimate was right" from "estimate was wrong",
# so tuning cannot fix these - the estimation step itself has to be
# replaced (see notes in find_crossing_circles / find_balloon_overlaps).
#
# Set either to True to re-enable for experimentation.
# Balloon-vs-balloon proximity path (older). Keep False - known-size check
# covers that. Geometry-overlap (balloon outline vs drawing detail) runs
# independently below via ENABLE_BALLOON_GEOMETRY_OVERLAP_CHECK.
ENABLE_BALLOON_OVERLAP_CHECK = False
# Balloon outline overlapping unrelated drawing geometry (flange circles,
# panel edges etc). Works via two-path foreign-segment detection inside
# find_balloon_circles - colour path AND spatial path for monotone drawings.
ENABLE_BALLOON_GEOMETRY_OVERLAP_CHECK = True
# Pure geometry circle crossing - OFF by default: needs performance tuning
# before batch deployment.
ENABLE_CIRCLE_CROSSING_CHECK = False

# SHAPE CLASH remains OFF pending further tuning.
ENABLE_SHAPE_CLASH_CHECK = False

# KNOWN-SIZE BOM balloon check - uses a real, supplied radius (5.25mm)
# instead of estimating one from segments, so none of the failure modes
# above (fragmented shapes, self-matches, inflated rects) apply. Covers
# ONLY the standard circular BOM balloon for now; other balloon shapes
# (oval ITEM/SECTION labels etc.) will get their own known size and their
# own switch once supplied.
ENABLE_KNOWN_SIZE_BALLOON_CHECK = True

# MEASURED-RECT balloon overlap - diameter-free. Uses the measured rect
# that find_balloon_circles already built from nearby drawing segments.
# OFF by default: was causing false positives on stacked/touching balloons
# (intentional drafting practice). Keep False until a suitable gap-tolerance
# is calibrated. The inscribed-radius cap below guards against oval inflation
# when this is re-enabled.
ENABLE_MEASURED_RECT_BALLOON_CHECK = False
MEASURED_RECT_MIN_OVERLAP_AREA_PT2 = 8.0
MEASURED_RECT_TANGENT_TOLERANCE_PT = 3.0
# Cap on effective radius from measured rect - prevents tall/oval balloon
# picking up nearby geometry and reporting an inflated r (confirmed:
# balloon '13' measured r=24pt, true ~12pt, falsely flagged '14').
MEASURED_RECT_MAX_EFFECTIVE_RADIUS_PT = 16.0

# ------------------------------------------------------------------
# Magenta / dangling-dimension detection
# ------------------------------------------------------------------
# In Inventor, dimensions that have lost their geometric association
# ("sick" / dangling dimensions) are conventionally displayed in
# magenta (1, 0, 1). Centerlines are often on a magenta layer too, so
# this check looks for magenta stroke clusters that look like
# DIMENSION structures (have both a longer dimension-line segment and
# shorter tick/extension geometry, and are not full-page centerlines).
ENABLE_MAGENTA_DIMENSION_CHECK = True
MAGENTA_R_MIN = 0.85
MAGENTA_G_MAX = 0.20
MAGENTA_B_MIN = 0.85
MAGENTA_MIN_SEGMENT_LENGTH_PT = 8.0
MAGENTA_CLUSTER_GAP_PT = 12.0
MAGENTA_MIN_CLUSTER_SEGMENTS = 3
MAGENTA_MAX_SPAN_FRACTION_OF_PAGE = 0.55
MAGENTA_HIGHLIGHT_COLOR = (0.85, 0.0, 0.85)

HIGHLIGHT_COLOR = (1.0, 0.0, 0.0)   # red - spelling and other content defects

# Line-crossing is a geometry finding about something ELSE crossing the
# word, not a claim that the word's own text is wrong - confirmed to
# cause real confusion (a correctly-spelled word like "SURFACES" or
# "ACCORDANCE" flagged for a line crossing it reads, at a glance in the
# marked-up PDF, identically to a genuine misspelling, since both used
# the exact same red box with nothing distinguishing them). A different
# color keeps that distinction visible without needing to read the report.
LINE_CROSSING_HIGHLIGHT_COLOR = (1.0, 0.55, 0.0)   # orange (highlight box)
CLASH_LABEL_COLOR = (0.60, 0.0, 0.0)               # dark red for CLASH label text
HIGHLIGHT_ALPHA = 0.45
HIGHLIGHT_SIZE_MULTIPLIER = 2.5
HIGHLIGHT_MAX_PAD_PT   = 2.5   # horizontal padding cap (pt)
HIGHLIGHT_MAX_PAD_PT_Y = 1.0   # vertical padding cap — keeps box tight to text height

# --- Line crossing (text/balloon cut by a drawing line) ---
CORE_INSET_FRACTION = 0.28
CORE_INSET_MIN_PT = 0.8
# A genuine line-crossing defect involves a small number of segments (a
# single table border, one leader line). Confirmed against real data that
# dense hatching/watermark/revision-cloud geometry can produce 40-400+
# crossing segments for ordinary text that has nothing to do with any
# defect - cap it well below that so only isolated, targeted crossings
# get flagged.
#
# MAX_LINE_CROSSING_SEGMENTS (per-word crossing-count cap) - RETIRED, no
# longer used anywhere. Originally meant to distinguish "a genuine
# targeted defect" from "dense hatching/watermark noise," but tuning it
# kept converging on the same failure: real, confirmed crossings kept
# landing just barely over whatever cap was set (11, then still 16 after
# raising it once), while genuine noise sits at 40-400+ - a huge gap this
# constant never needed to sit anywhere near the top of. Removed entirely
# rather than raised again, per explicit direction to prioritize catching
# every real crossing over avoiding some overkill highlighting. The
# WHOLE-PAGE version of this same idea (GEOMETRY_SANITY_* below) is kept,
# since an SHX-font AutoCAD file with literally every letter drawn as
# vector strokes is a categorically different, page-wide problem (100+
# flags burying the real ones) than any individual word's crossing count.
MAX_LINE_CROSSING_SEGMENTS = 15
# Sanity circuit-breaker for the whole page (see run_geometry_checks) - if
# combined line-crossing + balloon-overlap flags exceed both this fraction
# of total words AND this absolute floor, treat it as vector-outlined text
# rather than genuine defects
GEOMETRY_SANITY_MAX_FRACTION = 0.05
GEOMETRY_SANITY_MIN_ABSOLUTE = 25
# PAGE_EDGE_MARGIN_PT / ZONE_LABEL_MAX_CHARS - RETIRED as a line-crossing
# exclusion (see find_line_crossings). Zone-reference letters/numbers
# running along the sheet border (A-H down the sides, 1-12 across top/
# bottom) are SUPPOSED to sit right against the frame border line -
# standard convention on every drawing. This was a real, confirmed
# false-positive source on one drawing, but per explicit direction to
# prioritize catching every real crossing over avoiding overkill
# highlighting, removed along with the other per-word heuristic guesses
# rather than kept as a narrow carve-out.
PAGE_EDGE_MARGIN_PT = 35.0
ZONE_LABEL_MAX_CHARS = 3

# Dimension values, reference numbers in section/detail circles, and common
# drafting suffixes are SUPPOSED to sit directly on/against their dimension
# line, extension line, or leader - that's standard drafting convention, not
# a defect. Excluding these from the line-crossing check specifically
# (confirmed false-positiving on completely correct dimensioning: "240",
# "110 C/C", "6 PL", "2729 O/A" etc. all flagged purely for sitting on their
# own dimension/leader line as designed).
DIMENSION_SUFFIX_WORDS = {"C/C", "PL", "PL.", "TYP", "TYP.", "REF", "MIN", "MAX", "O/A", "CL", "=", "I/S", "O/S"}


def is_dimension_like(text):
    """A dimension number optionally decorated with a symbol - degree sign,
    diameter sign, minute/inch marks, a trailing period, comma thousands
    separator, etc. Strips ANY leading/trailing non-alphanumeric character
    generically rather than matching a fixed list of symbols, since
    different PDF exports/fonts render the same intended symbol (e.g. a
    degree sign) as different actual characters - confirmed against real
    data: one drawing used the Unicode degree sign, another substituted a
    plain tilde ('60~') for the same 60-degree angle callout, which a
    fixed-symbol-list regex missed entirely.
    """
    text = text.strip()
    if not text:
        return False
    if text.upper() in DIMENSION_SUFFIX_WORDS:
        return True
    core = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', text)
    # Plain digits, or comma-thousands-separated ("4,350") - confirmed on a
    # real drawing that large dimension values are sometimes written with
    # a thousands comma, which the plain \d+ pattern didn't match
    if re.fullmatch(r'\d{1,3}(,\d{3})*(\.\d+)?', core):
        return True
    if re.fullmatch(r'\d+(\.\d+)?', core):
        # The plain \d+ branch above has no digit-count limit, which
        # turned out to be too broad: confirmed on a real drawing that
        # it was matching 6-digit zero-padded reference numbers
        # ("001175", "001172", etc.) as if they were dimension values,
        # silently excluding them from line-crossing checks entirely.
        # A leading zero on a multi-digit whole number is a reliable
        # distinguishing signal here - nobody writes a real measured
        # dimension as "001175mm"; genuine dimensions are never
        # zero-padded, while formatted reference/ID codes commonly are.
        whole_part = core.split('.')[0]
        if len(whole_part) >= 2 and whole_part.startswith('0'):
            return False
        return True
    return False


def is_pure_punctuation(text):
    """True for tokens with no letters or digits at all - a lone '(' or
    ')' split off from a rotated bracketed dimension like '(4,350)' can
    never itself represent a spelling or content defect, so it's never
    worth flagging as a line-crossing target."""
    text = text.strip()
    return bool(text) and not any(c.isalnum() for c in text)



# Rotated/angled annotation text that follows its own reference line (e.g.
# a note running diagonally alongside a sloped edge, or a vertical margin
# label like "UP-STREAM REFERENCES") is also a false positive for the same
# reason as dimension text - it's deliberately placed on that line.
#
# is_likely_rotated() below is a cheap first-pass filter: for SOME exports
# a rotated word's own axis-aligned bounding box reflects the visual
# rotated extent, becoming much more square than a horizontal word's ever
# would - confirmed on one drawing: a rotated 7-letter word ("OPENING")
# measured a PERFECTLY SQUARE 45.6x45.6 box.
#
# It is NOT reliable on its own. For OTHER exports (confirmed on real
# drawings, a family of short vertical margin labels: "MAIN", "TANK",
# "MINIMUM", "FLOTATION", "PUMP", "DOWNCOMER"), each word's bounding box
# is reported "as read" - wide and short, aspect ratio 2.0-5.1, LOOKING
# EXACTLY LIKE NORMAL HORIZONTAL TEXT - even though the word is genuinely
# rotated 90 degrees on the page. Aspect ratio can't catch this.
#
# An earlier version of identify_rotated_lines() tried to infer rotation
# from how consecutive words on a line moved (Y-dominant flow = rotated).
# That only works if the exporter's mis-reported word coordinates happen
# to leak the rotation into the Y axis - confirmed NOT reliable: one
# drawing's "MAIN"/"TANK" pair had matching Y and differing X (the
# opposite pattern), so the flow heuristic missed it entirely and the
# words fell through to line-crossing as false positives.
#
# The robust fix is to stop inferring rotation from word positions at
# all and read it directly: page.get_text("dict") reports each line's
# actual writing-direction unit vector (line["dir"] = (cos, sin) of the
# text's own rendering matrix), independent of how that line's word
# boxes get reported. A near-horizontal line has dir close to (1,0) or
# (-1,0); anything else means the line is genuinely rotated on the page,
# regardless of which way a given exporter happens to scramble the word
# bounding boxes. block_no/line_no numbering from get_text("dict") lines
# up with the block_no/line_no fields returned by get_text("words"), so
# the resulting keys plug straight into the existing exclusion logic.
# ROTATED_TEXT_MIN_CHARS / ROTATED_TEXT_MAX_ASPECT and is_likely_rotated
# below - RETIRED as a line-crossing exclusion (see find_line_crossings).
# This was always a GUESS at rotation from aspect ratio alone, as opposed
# to in_rotated_line_group below, which uses PyMuPDF's own reported text
# direction - a verified fact. The guess had two confirmed false
# exclusions even after being tuned once (ITEM, Z1200, both misread as
# "rotated" purely from being short words in a normal font). The function
# is kept, unused, in case it's useful context again later - genuine
# rotated text stays protected via the ground-truth check regardless.
ROTATED_TEXT_MIN_CHARS = 4
ROTATED_TEXT_MAX_ASPECT = 0.7
ROTATED_LINE_DIR_Y_THRESHOLD = 0.3  # |sin(angle from horizontal)| - ~17 degrees
# How close a crossing segment's angle must be to the text's own writing
# direction before it's treated as "the line this text sits on" rather
# than a foreign line crossing it. Confirmed from real measured data: six
# false positives all had their crossing segment within 0.2 degrees of the
# text's own 35-degree baseline, while a genuine find ("R" crossed by a
# vertical line) was 90 degrees off. 12 degrees is comfortably wider than
# the measured noise and far narrower than any real crossing seen.
TEXT_BASELINE_PARALLEL_TOLERANCE_DEG = 12.0


def is_likely_rotated(text, rect):
    text = text.strip()
    if len(text) < ROTATED_TEXT_MIN_CHARS:
        return False
    w = rect.x1 - rect.x0
    h = rect.y1 - rect.y0
    if h <= 0:
        return False
    return (w / h) < ROTATED_TEXT_MAX_ASPECT


def identify_rotated_lines(page, words=None):
    """Returns a set of (block_no, line_no) keys for every text line that
    is genuinely rotated on the page, using PyMuPDF's own reported text
    direction (ground truth) rather than inferring rotation from word
    positions (which varies by exporter and isn't reliable - see the
    comment block above). Every word sharing one of these keys is part of
    a rotated label and should be excluded from line-crossing checks,
    whatever its own individual bounding box looks like.

    `words` is accepted but unused - kept so existing call sites don't
    need to change their signature elsewhere.
    """
    rotated_keys = set()
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type", 0) != 0:  # 0 = text block, 1 = image block
            continue
        block_no = block.get("number")
        for line_no, line in enumerate(block.get("lines", [])):
            dir_x, dir_y = line.get("dir", (1.0, 0.0))
            if abs(dir_x) < 1e-6 or abs(dir_y) > ROTATED_LINE_DIR_Y_THRESHOLD * max(abs(dir_x), 1e-6):
                rotated_keys.add((block_no, line_no))
    return rotated_keys


def map_line_directions(page):
    """Returns a list of (line_bbox, angle_degrees) giving the actual
    writing direction of every text line, from PyMuPDF's own reported
    "dir" vector (ground truth, not inferred from bounding boxes).

    Deliberately returns POSITION-keyed data (each line's bbox) rather
    than a dict keyed by (block_no, line_no). Confirmed necessary: an
    earlier version keyed on those numbers and never matched a single
    word, because get_text("dict") numbers blocks including image blocks
    while get_text("words") numbers only text blocks - so the two
    schemes drift apart on any page containing an image. Position can't
    drift; a word either falls inside a line's bbox or it doesn't.

    Used by find_line_crossings to tell apart:
      - a foreign line genuinely crossing through a word  (flag it), and
      - the dimension line the word is SITTING ON         (don't flag it).

    Confirmed necessary on a real drawing: six dimension values ("600",
    "TYP", "513", "747", "605", "4113") on a 35-degree sloped detail were
    all flagged, every one of them by a segment measured at exactly -35
    degrees - i.e. the very dimension line each value labels. Rotated text
    has a near-square axis-aligned bounding box (measured aspect 1.04-1.10
    for these), so its own dimension line passes diagonally through that
    inflated box and reads as a crossing even though nothing visually
    touches the glyphs.

    Angle is normalised to 0-180 (direction, not sense) so a line and its
    reverse compare equal.
    """
    line_dirs = []
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type", 0) != 0:
            continue
        for line in block.get("lines", []):
            bbox = line.get("bbox")
            if not bbox:
                continue
            dir_x, dir_y = line.get("dir", (1.0, 0.0))
            angle = math.degrees(math.atan2(dir_y, dir_x)) % 180.0
            line_dirs.append((fitz.Rect(bbox), angle))
    return line_dirs


def text_angle_at(line_dirs, word_rect):
    """Returns the writing-direction angle of the text line containing
    this word, or None if no line contains it. Matches by position (which
    line's bbox contains the word's centre) rather than by block/line
    numbers - see map_line_directions for why."""
    cx = (word_rect.x0 + word_rect.x1) / 2
    cy = (word_rect.y0 + word_rect.y1) / 2
    for bbox, angle in line_dirs:
        if bbox.x0 <= cx <= bbox.x1 and bbox.y0 <= cy <= bbox.y1:
            return angle
    return None


def segment_parallel_to_text(p1, p2, text_angle_deg, tolerance_deg):
    """True if the segment runs roughly parallel to the given text writing
    direction - meaning it is almost certainly the dimension/leader line
    the text sits on, not a foreign line crossing it."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return False
    seg_angle = math.degrees(math.atan2(dy, dx)) % 180.0
    diff = abs(seg_angle - text_angle_deg) % 180.0
    if diff > 90.0:
        diff = 180.0 - diff
    return diff <= tolerance_deg


# --- Text-on-text overlap ---
# Lowered from 0.6/0.6 after real diagnostic data: a genuinely-overlapping
# dimension pair ("2360" over "(3284) O/A") measured x_overlap=0.52,
# y_overlap=0.58 - real, visually-confirmed overlap that fell just short
# of the old threshold. Checked every OTHER near-miss on the same page
# before lowering anything: nothing else came anywhere close to
# y_overlap=0.55 (the next highest was 0.50, from "APPROVED"/"FOR" in a
# title-block stamp - ordinary adjacent stamp text, not a defect). Y at
# 0.55 catches the real case while staying safely above that boundary;
# X needs to go lower (down to 0.5) purely to admit this pair's 0.52.
#
# Y lowered again, from 0.55 to 0.51, after a SECOND confirmed real case
# on a different drawing: '64' vs '90°' measured y_overlap=0.52 - just
# under the 0.55 bar. 0.51 sits directly between this new confirmed case
# (0.52, should flag) and the previously-confirmed non-case (APPROVED/
# FOR at 0.50, should not flag) - the narrowest gap available given both
# confirmed data points, but a real, evidence-backed value rather than a
# guess.
# X lowered again, from 0.5 to 0.25, after a confirmed real case: two
# separate "187" dimension labels measured x_overlap=0.27 - a real,
# user-confirmed overlap. Checked every other near-miss on the same page
# X lowered from 0.5 to 0.25 after a confirmed real case: two separate
# "187" dimension labels measured x_overlap=0.27.
#
# NOTE: an earlier version of this comment described the "PLACES"/"PER"/
# "PLATFORM" near-misses on this same page as ordinary non-defect running
# text - that was wrong. A screenshot later confirmed they're a genuine
# duplicate-overlap defect (the entire note paragraph rendered twice,
# overlapping). See TEXT_OVERLAP_Y_FRACTION_CROSS_BLOCK below for how
# that's actually handled - a same-block/cross-block distinction, not a
# single Y number, since the confirmed real case (0.36-0.47) sits BELOW
# the confirmed non-case ("APPROVED"/"FOR", same block, 0.50).
TEXT_OVERLAP_X_FRACTION = 0.25
TEXT_OVERLAP_Y_FRACTION = 0.51
# Applies only when the two words come from genuinely different text
# blocks whose block-level areas substantially overlap (see
# find_text_overlaps) - set below both confirmed real cross-block cases
# (0.36, 0.47) while still requiring a real, meaningful overlap rather
# than an incidental touch.
TEXT_OVERLAP_Y_FRACTION_CROSS_BLOCK = 0.3
# How much of the SMALLER block's area must intersect the other block
# before the permissive cross-block threshold above applies. Normal
# adjacent paragraphs/lines only touch at their edges (a few percent of
# area at most, even for tightly-spaced small print); a genuine
# duplicate-overlay (one whole paragraph rendered atop another,
# confirmed real via screenshot) is substantially coincident. 0.3 sits
# well between those two regimes.
CROSS_BLOCK_MIN_BLOCK_OVERLAP_FRACTION = 0.3
TEXT_OVERLAP_MIN_CHARS = 2  # Reverted from 4. Raising it to 4 was meant as
# extra insurance against title-block prose noise ("are", "all", "the"),
# but the entirely-lowercase filter below already handles those, and the
# raise silently killed confirmed real dimension overlaps that are shorter
# than 4 characters: "187"/"187" (3 chars), "64"/"90°" (2 and 3 chars).
# Those had been verified working earlier and stopped firing without any
# report entry to show why - they were dropped before the overlap maths
# ever ran. 2 is the correct floor: it only excludes single characters.
# How close two same-text words' top-left corners must be to be treated
# as the SAME fake-bold duplicate glyph trick (see find_text_overlaps) -
# confirmed real duplicates sit at exactly identical coordinates, so this
# just needs to be small enough to safely exclude two genuinely separate
# same-value labels (confirmed ~14pt apart in one real case) from being
# mistaken for the same thing.
FAKE_BOLD_POSITION_TOLERANCE_PT = 2.0

# --- Balloon-vs-balloon overlap ---
BALLOON_SEARCH_MARGIN = 5.0
BALLOON_MIN_SEGMENTS = 12
# Fallback search margins, tried only when the normal 5pt margin finds
# too little - see find_balloon_circles for why this is a second,
# bounded attempt rather than a blanket widening (a prior attempt at
# this used the PDF's own internal "block" grouping instead and caused a
# severe regression, sweeping in unrelated content on busy pages).
#
# Two real, quantified data points went into these numbers, not guesses:
# a circular/multi-line-text balloon needed extra vertical reach (a
# stacked item-number-over-reference-number layout), while a SEPARATE,
# oval/"stadium" balloon shape (built from just 2 rounded end-caps and 3
# straight lines - a far more efficient convention than a circle
# approximated with dozens of tiny segments) turned out to need much
# more HORIZONTAL reach instead - a real raw geometry dump measured the
# oval extending 31.9pt beyond the digit on each side, while vertically
# the digit's own height already nearly matched the shape's (needing
# only 18.7pt of extra reach, comfortably under the existing Y margin).
# Both dimensions are widened together now, each with real headroom
# above its own confirmed-needed value.
BALLOON_TALL_SEARCH_MARGIN_Y_PT = 20.0
BALLOON_TALL_SEARCH_MARGIN_X_PT = 35.0
# How close to exactly 0/90 degrees a segment's angle must be to still
# count as "axis-aligned" (see find_balloon_circles) - a small tolerance
# for near-horizontal/near-vertical segments that are still genuinely
# orthogonal drafting lines, not meaningfully diagonal/curved geometry.
BALLOON_AXIS_TOLERANCE_DEG = 5.0
# BALLOON_MIN_DIAMETER / MAX_DIAMETER / ASPECT_MIN / ASPECT_MAX (precise
# measured-shape thresholds) retired - see find_balloon_circles. Trying
# to correctly reconstruct an accurate circle outline from raw line/curve
# segments turned out to be fragile in a way that kept resurfacing across
# several different, unrelated causes (curve-vs-line construction,
# segment-inclusion test choice, unrelated precision improvements
# elsewhere) - none of which was ever actually necessary for what this
# is used for, which only needs to know roughly where a balloon sits, not
# its exact shape.
BALLOON_ASSUMED_PADDING_PT = 5.0  # matches BALLOON_SEARCH_MARGIN - a
# reasonable stand-in for "how far a balloon's circle typically extends
# beyond the digit it contains", based on typical balloon sizes observed
# across many real drawings throughout this tool's development.
# Maximum distance the balloon rect is allowed to extend beyond the digit's
# own bounding box on any side. The wide fallback search (35pt X-margin)
# can reach an adjacent balloon's segments when the two are close together,
# inflating the measured rect to nearly double the real circle size and
# creating false overlap flags. Sized above the largest confirmed real
# balloon extension (31.9pt from one geometry dump) but well below 35pt
# so adjacent balloons can't contribute their geometry to each other's
# rect measurement.
BALLOON_MAX_RECT_MARGIN_PT = 33.0
# A few stray, differently-colored segments within a balloon's rect could
# just be incidental (e.g. a single unrelated line grazing the edge) -
# require a real cluster before treating it as genuine overlap with
# unrelated geometry. Confirmed on a real drawing: a genuine overlap
# case had dozens of foreign-colored segments within the balloon's rect
# (a rectangular panel edge plus a dense hatching/thread pattern), not
# just one or two - this threshold is set well below that confirmed
# case while still requiring more than an incidental single stray line.
BALLOON_FOREIGN_SEGMENT_MIN = 3

# BOM label placement constants.
# BOM_LABEL_OFFSET_X_PT: how far to the LEFT of the ITEM column edge to
#   place "?" (no-balloon) and "N?" (missing-sequence) labels.  Large enough
#   to sit clearly outside the BOM table border.
BOM_LABEL_OFFSET_X_PT = 35.0
# BOM_LABEL_MIN_SPACING_PT: minimum vertical gap between any two BOM labels
#   in the same margin.  When consecutive issues share close row positions the
#   labels are staggered so they don't overprint each other.
BOM_LABEL_MIN_SPACING_PT = 16.0
# Maximum radius (pt) for a balloon to qualify for the geometry-overlap
# check.  Standard BOM balloon is 5.25mm = ~14.87pt radius; anything
# beyond this threshold is more likely a large mechanical circle (bore,
# flange, pipe cross-section) whose interior happens to contain a number,
# not a real BOM callout balloon.  35pt ≈ 12.4mm gives generous clearance
# above the standard while still rejecting large false positives.
BALLOON_MAX_GEOMETRY_OVERLAP_RADIUS_PT = 35.0
# BALLOON_OVERLAP_FACTOR (distance-vs-radius model) retired - see
# find_balloon_overlaps, now using literal bounding-box intersection
# (BALLOON_OVERLAP_X_FRACTION / BALLOON_OVERLAP_Y_FRACTION) instead.

# A loosened, aspect/size-based "balloon-like" gate for line-crossing
# exemption purposes (as opposed to find_balloon_circles' precise
# balloon-overlap gate) was tried and abandoned here. It was meant to
# fix a real, confirmed regression: an unrelated, separately-verified
# fix elsewhere (more accurate bezier curve sampling) shifted two
# genuine balloons' measured aspect ratio from 1.35/1.38 to 1.90/2.25,
# just outside the strict 0.65-1.55 range, silently breaking their
# line-crossing exemption. But tested against the real data before
# shipping, no aspect-ratio range could include those two without ALSO
# including three separately-confirmed non-balloon candidates whose
# aspect ratios (1.72/1.79/1.82) sit strictly BETWEEN the "good" values
# and the strict range - shape/size alone can't distinguish "genuine
# balloon measured slightly off" from "genuinely not a balloon" here.

# --- BOM header detection ---
COLUMN_MARGIN_PT = 6.0
HEADER_ROW_TOLERANCE_PT = 3.0

# See extract_item_column() - keeps only the largest contiguous run of
# evenly-spaced rows in a candidate ITEM column, dropping stray
# same-x-band digits from elsewhere on the page. A genuine row-to-row gap
# is typically a handful of points (one text line); the floor and
# multiplier below just need to comfortably clear normal row-height
# variation while still rejecting a gap of hundreds of points to an
# unrelated word.
ROW_CLUSTER_MIN_GAP_PT = 25.0
ROW_CLUSTER_GAP_MULTIPLIER = 3.0

# --- Revision stamp check (REV letter/number vs PRELIMINARY/APPROVED stamp) ---
# Bottom-right corner region, as a fraction of page width/height - shared by
# the stamp check and the REV-compare check below, both of which locate the
# main title block's REV field by position rather than by pairing with a
# neighbouring word (proved more reliable on real drawings). Loosened from
# 0.65/0.75 after a real drawing's corner REV wasn't found despite sitting
# in the expected corner area - some client-specific title-block variants
# position it slightly differently than the standard template. Still well
# clear of a revisions table's own REV column, which sits far to the left
# (~x=200-230 on a similar page) in every template checked so far.
CORNER_X_FRACTION = 0.55
CORNER_Y_FRACTION = 0.65
# How far (points) from a stamp anchor word ("APPROVED"/"PRELIMINARY") to
# search for its companion words. This is a FLOOR, not a fixed value - see
# STAMP_SEARCH_MARGIN_HEIGHT_MULT below for why.
STAMP_SEARCH_MARGIN = 30.0

# Companion-word search margin also scales with the anchor word's own
# rendered height, in addition to the flat floor above. A page produced by
# a different export pipeline (confirmed on a real file: "Producer:
# Microsoft: Print To PDF" instead of the usual native CAD/Inventor
# export) can render the whole title block - font size, line spacing,
# everything - at a different scale, which stretches the physical gap
# between "APPROVED" and "FOR CONSTRUCTION" past a fixed-point margin even
# though it's the exact same 2-line stamp layout. Scaling the margin by
# the anchor's own text height tracks that automatically: a typical ~10pt
# title-block font with a 30pt margin gives roughly a 3x multiple, so that
# ratio is used as the basis instead of hard-coding one absolute number
# that only fits one export pipeline's font size.
STAMP_SEARCH_MARGIN_HEIGHT_MULT = 3.0

# --- REV compare check (corner REV vs revisions-table REV) ---
# How close (points) "REV", "BY" and "DATE" must be vertically to count as
# being on the same revisions-table header row
TABLE_ROW_TOLERANCE_PT = 3.0


def load_ignore_words():
    """Load extra words from SpellCheckIgnoreWords.txt."""
    extra = set()
    p = Path(IGNORE_FILE)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip().lower()
                if word and not word.startswith("#"):
                    extra.add(word)
        print(f"  Loaded {len(extra)} custom ignore word(s) from: {p}")
        # Debug - check if certificado is in there
        if "certificado" in extra:
            print("  [OK] CERTIFICADO found in ignore list")
        else:
            print("  [!] CERTIFICADO NOT found in ignore list")
    else:
        print(f"  Note: Ignore file not found at: {p}")
    return extra


def clean_token(word):
    """
    Strip non-alpha characters from edges.
    Discard entirely if any non-alpha character remains anywhere in the token.
    This catches: SSFM18-115 -> "", AS1234 -> "", P&ID -> ""
    Pure alpha strings like ASSEMBLY, SEMBLY are returned as-is.
    """
    stripped = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", word)
    if re.search(r"[^A-Za-z]", stripped):
        return ""
    return stripped


def split_into_valid_words(token, spell, min_part=3):
    """
    Try to split a token into valid dictionary words using dynamic programming.
    Returns True if the token can be fully decomposed into real words.
    e.g. MECHANICALENG -> MECHANICAL + ENG -> True
         ISSUEDFORCONSTRUCTION -> ISSUED + FOR + CONSTRUCTION -> True
         PROKECT -> cannot be split into valid words -> False
    """
    token = token.lower()
    n     = len(token)
    # dp[i] = True means token[0:i] can be split into valid words
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(max(0, i - 20), i):
            if dp[j]:
                part = token[j:i]
                if len(part) >= min_part and part in spell:
                    dp[i] = True
                    break
    return dp[n]


def is_candidate(raw_token, all_ignore):
    """
    Return True if this token should be spell-checked.
    raw_token is the original text directly from the PDF (correct case).
    """
    if not raw_token:
        return False
    # Must be fully UPPERCASE - skips Titlecase and lowercase
    if not raw_token.isupper():
        return False
    # Must be at least 4 characters
    if len(raw_token) <= 3:
        return False
    # Skip long tokens - concatenated phrases stored without spaces in PDF
    # e.g. MECHANICALENG, ISSUEDFORCONSTRUCTION, GENERALARRANGEMENT
    # Real English words are almost never longer than 20 characters
    if len(raw_token) > 20:
        return False
    # Skip tokens with only one unique character (AAAA, IIII etc.)
    if len(set(raw_token)) == 1:
        return False
    # Skip if in ignore list
    if raw_token.lower() in all_ignore:
        return False
    return True


def pick_pdfs():
    """Windows native multi-select file picker."""
    MAX = 32768
    buf = ctypes.create_unicode_buffer(MAX)

    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ("lStructSize",       wintypes.DWORD),
            ("hwndOwner",         wintypes.HWND),
            ("hInstance",         ctypes.c_void_p),
            ("lpstrFilter",       ctypes.c_wchar_p),
            ("lpstrCustomFilter", ctypes.c_wchar_p),
            ("nMaxCustFilter",    wintypes.DWORD),
            ("nFilterIndex",      wintypes.DWORD),
            ("lpstrFile",         ctypes.c_wchar_p),
            ("nMaxFile",          wintypes.DWORD),
            ("lpstrFileTitle",    ctypes.c_wchar_p),
            ("nMaxFileTitle",     wintypes.DWORD),
            ("lpstrInitialDir",   ctypes.c_wchar_p),
            ("lpstrTitle",        ctypes.c_wchar_p),
            ("Flags",             wintypes.DWORD),
            ("nFileOffset",       wintypes.WORD),
            ("nFileExtension",    wintypes.WORD),
            ("lpstrDefExt",       ctypes.c_wchar_p),
            ("lCustData",         ctypes.c_longlong),
            ("lpfnHook",          ctypes.c_void_p),
            ("lpTemplateName",    ctypes.c_wchar_p),
            ("pvReserved",        ctypes.c_void_p),
            ("dwReserved",        wintypes.DWORD),
            ("FlagsEx",           wintypes.DWORD),
        ]

    OFN_PATHMUSTEXIST    = 0x00000800
    OFN_FILEMUSTEXIST    = 0x00001000
    OFN_ALLOWMULTISELECT = 0x00000200
    OFN_EXPLORER         = 0x00080000

    ofn             = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.lpstrFilter = "PDF Files\0*.pdf\0All Files\0*.*\0"
    ofn.lpstrFile   = ctypes.cast(buf, ctypes.c_wchar_p)
    ofn.nMaxFile    = MAX
    ofn.lpstrTitle  = "Select PDF(s) to Spell-Check  (hold Ctrl for multiple)"
    ofn.Flags       = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST | OFN_ALLOWMULTISELECT | OFN_EXPLORER

    if not ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return []

    parts   = []
    current = []
    for ch in buf[:]:
        if ch == "\x00":
            word = "".join(current).strip()
            if word:
                parts.append(word)
            elif current:
                break
            current = []
        else:
            current.append(ch)

    if not parts:
        return []
    elif len(parts) == 1:
        return [parts[0]]
    else:
        folder = parts[0]
        return [str(Path(folder) / f) for f in parts[1:]]


def show_message(title, msg, error=False):
    icon = 0x10 if error else 0x40
    ctypes.windll.user32.MessageBoxW(0, msg, title, icon)


def draw_highlight(page, rect, enlarge=True, color=None, label=None,
                   label_color=None, label_fontsize=None, label_offset_lines=2.0):
    """Draw the standard highlight over a rect, optionally enlarging
    it (capped) so it's more noticeable than the word's own bounding box.
    `color` defaults to HIGHLIGHT_COLOR (red, spelling/content defects);
    pass a different color for check categories that aren't a defect in
    the word's own text - e.g. LINE_CROSSING_HIGHLIGHT_COLOR - so opening
    the marked-up PDF doesn't read as "this word is misspelled" when the
    actual finding is "something else crosses through this word".

    `label` (e.g. "CLASH") is drawn just below the highlight so geometry
    findings are visually distinct from spelling marks on the marked-up PDF.
    `label_color` overrides the label text colour (defaults to `color`).
    `label_fontsize` overrides the label text size (defaults to 7.0pt).
    """
    if color is None:
        color = HIGHLIGHT_COLOR
    if enlarge:
        w = rect.x1 - rect.x0
        h = rect.y1 - rect.y0
        pad_x = min(w * (HIGHLIGHT_SIZE_MULTIPLIER - 1) / 2, HIGHLIGHT_MAX_PAD_PT)
        pad_y = min(h * (HIGHLIGHT_SIZE_MULTIPLIER - 1) / 2, HIGHLIGHT_MAX_PAD_PT_Y)
        rect = fitz.Rect(rect.x0 - pad_x, rect.y0 - pad_y, rect.x1 + pad_x, rect.y1 + pad_y)
    # PyMuPDF word rects include line-spacing above/below the glyphs.
    # Trim 20 % from top and bottom so the highlight hugs the visible text.
    trim_y = (rect.y1 - rect.y0) * 0.20
    rect = fitz.Rect(rect.x0, rect.y0 + trim_y, rect.x1, rect.y1 - trim_y)
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(
        fill=color, color=color,
        fill_opacity=HIGHLIGHT_ALPHA, stroke_opacity=0,
    )
    shape.commit()
    if label:
        _lfs = label_fontsize if label_fontsize is not None else 7.0
        _lc  = label_color   if label_color   is not None else color
        text_y = min(rect.y1 + _lfs * label_offset_lines, page.rect.y1 - 2.0)
        # Estimate label width (~0.6 × fontsize per character for Helvetica)
        # and shift left if it would overflow the right page edge.
        est_label_w = len(label) * _lfs * 0.6
        text_x = max(rect.x0, page.rect.x0 + 1.0)
        if text_x + est_label_w > page.rect.x1 - 2.0:
            text_x = max(page.rect.x1 - est_label_w - 2.0, page.rect.x0 + 1.0)
        page.insert_text(
            (text_x, text_y),
            label,
            fontsize=_lfs,
            fontname="helv",
            color=_lc,
        )


# ==================================================================
# CHECK 1: line crossing / text overlap / balloon overlap
# ==================================================================

def _orientation(p, q, r):
    val = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if val > 1e-9:
        return 1
    if val < -1e-9:
        return -1
    return 0


def _on_segment(p, q, r):
    return (min(p[0], r[0]) - 1e-6 <= q[0] <= max(p[0], r[0]) + 1e-6 and
            min(p[1], r[1]) - 1e-6 <= q[1] <= max(p[1], r[1]) + 1e-6)


def segments_intersect(p1, p2, p3, p4):
    o1 = _orientation(p1, p2, p3)
    o2 = _orientation(p1, p2, p4)
    o3 = _orientation(p3, p4, p1)
    o4 = _orientation(p3, p4, p2)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(p1, p3, p2):
        return True
    if o2 == 0 and _on_segment(p1, p4, p2):
        return True
    if o3 == 0 and _on_segment(p3, p1, p4):
        return True
    if o4 == 0 and _on_segment(p3, p2, p4):
        return True
    return False


def rect_contains_point(rect, pt, tol=0.0):
    return (rect.x0 - tol <= pt[0] <= rect.x1 + tol and
            rect.y0 - tol <= pt[1] <= rect.y1 + tol)


def segment_intersects_rect(p1, p2, rect):
    p1 = (p1[0], p1[1])
    p2 = (p2[0], p2[1])
    if rect_contains_point(rect, p1) or rect_contains_point(rect, p2):
        return True
    corners = [
        (rect.x0, rect.y0), (rect.x1, rect.y0),
        (rect.x1, rect.y1), (rect.x0, rect.y1),
    ]
    for i in range(4):
        if segments_intersect(p1, p2, corners[i], corners[(i + 1) % 4]):
            return True
    return False


def bezier_point(p0, p1, p2, p3, t):
    """Standard cubic bezier formula - the actual curve position at
    parameter t (0 to 1), not to be confused with the control points
    themselves, which sit OFF the curve (that's how bezier curves bend
    at all) - see extract_segments for why this distinction matters."""
    mt = 1 - t
    x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
    y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
    return (x, y)


BEZIER_SAMPLE_COUNT = 8  # points sampled along each curve, connected as short straight segments


def extract_segments(drawing, crude_curves=False):
    meta_base = {
        "type": drawing.get("type"),
        "color": drawing.get("color"),
        "fill": drawing.get("fill"),
        "stroke_opacity": drawing.get("stroke_opacity"),
        "fill_opacity": drawing.get("fill_opacity"),
        "width": drawing.get("width"),
    }
    segments = []
    for item in drawing.get("items", []):
        kind = item[0]
        # "src_kind" (l/c/re/qu - which raw PDF drawing primitive this
        # segment came from) added to a shallow per-item copy of meta.
        # Diagnostic value only for now - lets us directly verify what a
        # given balloon's nearby geometry is actually built from, rather
        # than assuming. Confirmed necessary: a real regression was
        # chased for several rounds under the assumption balloon circles
        # are drawn with bezier curves (the only thing crude_curves
        # affects) - if they're actually built from straight "l" segments
        # instead, as a separate reference script's own documentation
        # claims for real Inventor exports, that whole theory would be
        # chasing the wrong mechanism entirely, and this is how to know
        # for certain instead of continuing to guess.
        meta = {**meta_base, "src_kind": kind}
        if kind == "l":
            p1, p2 = item[1], item[2]
            segments.append(((p1.x, p1.y), (p2.x, p2.y), meta))
        elif kind == "c":
            if crude_curves:
                # Balloon-shape detection specifically needs this OLDER,
                # cruder approximation (connecting the 4 raw control
                # points as 3 straight chords) rather than the accurate
                # sampling below. Confirmed on a real drawing: the
                # balloon-detection aspect/size thresholds were
                # calibrated against this exact crude approximation
                # (matching a separate, never-updated reference script
                # that still uses it) - switching balloon detection to
                # the more accurate sampling shifted several genuine
                # balloons' measured shape enough to fail those
                # thresholds, even though the thresholds themselves were
                # never wrong. Line-crossing genuinely needs the accurate
                # version (see below) since it must know precisely where
                # a curve is to correctly detect a crossing - but balloon
                # shape detection just needs a rough, CONSISTENT circle
                # outline, and using the same measurement basis the
                # thresholds were tuned against is more important there
                # than curve precision.
                pts = [(p.x, p.y) for p in item[1:5]]
                for i in range(len(pts) - 1):
                    segments.append((pts[i], pts[i + 1], meta))
            else:
                # Confirmed on a real drawing: connecting the four raw bezier
                # CONTROL points as straight lines (the old approach) can
                # deviate several points from where the true curve actually
                # is - control points sit off the curve by design, that's
                # how a bezier bends. For a circular/arc shape (a clamp band,
                # in this case), that gap was enough to make a genuine visual
                # crossing through a word invisible to the intersection test,
                # since the crude approximation simply wasn't near the word
                # at all even though the real curve was. Sampling the actual
                # curve at several points and connecting THOSE instead tracks
                # the true path closely.
                p0, p1, p2, p3 = [(p.x, p.y) for p in item[1:5]]
                sampled = [bezier_point(p0, p1, p2, p3, i / BEZIER_SAMPLE_COUNT) for i in range(BEZIER_SAMPLE_COUNT + 1)]
                for i in range(len(sampled) - 1):
                    segments.append((sampled[i], sampled[i + 1], meta))
        elif kind == "re":
            r = item[1]
            corners = [(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)]
            for i in range(4):
                segments.append((corners[i], corners[(i + 1) % 4], meta))
        elif kind == "qu":
            q = item[1]
            pts = [(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y)]
            for i in range(4):
                segments.append((pts[i], pts[(i + 1) % 4], meta))
    return segments


# Real drawings can have tens of thousands of tiny line segments (hatching,
# dashed lines, polygon-approximated circles etc.) - testing every word
# against every single segment is O(words x segments) and measured ~95
# SECONDS on a single real page (610 words x 56,000 segments). A spatial
# grid index cuts this to ~0.015s by only checking segments that are
# actually near each word - each word ends up testing ~8 candidates on
# average instead of 56,000.
GRID_CELL_SIZE = 20.0  # points - tune if drawings use very different scales


def is_white_ish(rgb, threshold=0.92):
    if not rgb:
        return False
    return all(c >= threshold for c in rgb)


def meta_has_visible_stroke(meta):
    dtype = meta.get("type") or ""
    stroke_color = meta.get("color")
    stroke_opacity = meta.get("stroke_opacity")
    stroke_width = meta.get("width")
    return (
        "s" in dtype
        and stroke_color is not None
        and not is_white_ish(stroke_color)
        and (stroke_opacity is None or stroke_opacity > 0.02)
        and (stroke_width is None or stroke_width > 0)
    )


def meta_has_visible_fill(meta):
    dtype = meta.get("type") or ""
    fill_color = meta.get("fill")
    fill_opacity = meta.get("fill_opacity")
    return (
        "f" in dtype
        and fill_color is not None
        and not is_white_ish(fill_color)
        and (fill_opacity is None or fill_opacity > 0.02)
    )


def drawing_is_visible(d):
    """A path from page.get_drawings() only corresponds to something a
    person can actually see if it has a real stroke or fill: nonzero
    opacity, a color that isn't white-on-white, and (for strokes) a
    nonzero line width. Markup/annotation tools commonly leave invisible
    geometry behind - zero-opacity highlight boxes, white "hit target"
    rectangles, zero-width construction rectangles - which are real paths
    in the PDF's content stream but were never actually drawn on the
    page. Confirmed on a real file (from a markup/redline tool, going by
    its filename): plain NOTES paragraph text with nothing visibly
    touching it at all still had "crossing segments" detected, which
    only makes sense if invisible geometry was being counted as if it
    were a visible line."""
    return meta_has_visible_stroke(d) or meta_has_visible_fill(d)


def build_segment_index(page, crude_curves=False, drawings=None):
    """Build the page's segment list ONCE, plus a spatial grid mapping
    (cell_x, cell_y) -> list of segment indices, so both the line-crossing
    and balloon-circle checks can do fast proximity lookups instead of
    scanning every segment on the page.

    crude_curves=True builds a SEPARATE index using the older, cruder
    bezier approximation - used for balloon-shape detection specifically,
    since its thresholds were calibrated against that approximation (see
    extract_segments). Line-crossing keeps using the default, accurate
    index; balloon detection gets its own separate one built with this
    flag set.

    drawings: if the caller already fetched page.get_drawings() (e.g. to
    share it between the line-crossing and balloon indexes), pass it here
    and the expensive get_drawings() call is skipped. Both indexes can
    share the SAME raw drawings list - they differ only in how extract_segments
    processes each drawing's curves, not in what drawings are fetched."""
    if drawings is None:
        drawings = page.get_drawings()
    segments = []
    for d in drawings:
        if not drawing_is_visible(d):
            continue
        segments.extend(extract_segments(d, crude_curves=crude_curves))

    grid = {}
    for idx, (p1, p2, meta) in enumerate(segments):
        x0, x1 = (p1[0], p2[0]) if p1[0] <= p2[0] else (p2[0], p1[0])
        y0, y1 = (p1[1], p2[1]) if p1[1] <= p2[1] else (p2[1], p1[1])
        cx0, cx1 = int(x0 // GRID_CELL_SIZE), int(x1 // GRID_CELL_SIZE)
        cy0, cy1 = int(y0 // GRID_CELL_SIZE), int(y1 // GRID_CELL_SIZE)
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                grid.setdefault((cx, cy), []).append(idx)

    return segments, grid


def segments_near_rect(segments, grid, x0, y0, x1, y1):
    """Return the (deduplicated) list of (p1, p2, meta) segments in grid
    cells touching the given rect - the fast candidate set instead of all
    segments on the page."""
    cx0, cx1 = int(x0 // GRID_CELL_SIZE), int(x1 // GRID_CELL_SIZE)
    cy0, cy1 = int(y0 // GRID_CELL_SIZE), int(y1 // GRID_CELL_SIZE)
    seen = set()
    for cx in range(cx0, cx1 + 1):
        for cy in range(cy0, cy1 + 1):
            for idx in grid.get((cx, cy), ()):
                seen.add(idx)
    return [segments[i] for i in seen]


def shrink_rect(rect):
    h = rect.y1 - rect.y0
    inset = max(h * CORE_INSET_FRACTION, CORE_INSET_MIN_PT)
    w = rect.x1 - rect.x0
    inset_x = min(inset, w * 0.45)
    inset_y = min(inset, h * 0.45)
    return fitz.Rect(rect.x0 + inset_x, rect.y0 + inset_y,
                      rect.x1 - inset_x, rect.y1 - inset_y)


# A steeply vertical crossing segment is almost always a centerline or
# reference-line mark, not a defect - see find_line_crossings for the
# reasoning
VERTICAL_SEGMENT_MAX_DX_RATIO = 0.15

# A genuine centerline mark is short - just long enough to mark the
# specific feature it labels. Lowered again after a SECOND confirmed
# case: a reference number ("001174") was genuinely crossed by a 136.5pt
# vertical segment - well under the previous 150pt cap, so it was still
# being treated as a legitimate short centerline and excluded. Combined
# with the earlier confirmed case (a ~807pt page-spanning grid line),
# both known bad exclusions are now far above this new cap; there isn't
# yet a confirmed real "legitimate short centerline" measurement on
# record to calibrate the lower bound precisely against, so 50pt was
# chosen as comfortably below both confirmed-bad cases while still being
# long enough to cover a real centerline mark extending a bit past the
# feature it labels.
VERTICAL_SEGMENT_MAX_LENGTH_PT = 50.0


def is_steeply_vertical_segment(p1, p2):
    dx = abs(p2[0] - p1[0])
    dy = abs(p2[1] - p1[1])
    if dy <= 0:
        return False
    if dy > VERTICAL_SEGMENT_MAX_LENGTH_PT:
        return False
    return dx <= VERTICAL_SEGMENT_MAX_DX_RATIO * dy


def find_line_crossings(page, segments, grid, exclude_regions=None, balloon_word_keys=None, report_lines=None, words=None):
    # words can be passed in explicitly - see run_geometry_checks, which
    # now extracts it ONCE and shares it across every check on the page
    # instead of each function calling page.get_text("words") separately.
    # Confirmed necessary on a real drawing: a balloon "8" that
    # find_balloon_circles correctly recognized was STILL not being
    # matched here even after switching to a "stable" (block, line, word)
    # number key - meaning the two independent get_text("words") calls
    # weren't actually returning consistent numbering for the same word,
    # likely because several highlight-drawing operations from earlier
    # checks run on this same page in between the two calls. A single
    # shared extraction removes the possibility of that mismatch entirely,
    # rather than trying to make the matching key more "stable" a second
    # time.
    if words is None:
        words = page.get_text("words")
    if not words or not segments:
        return []
    exclude_regions = exclude_regions or []
    balloon_word_keys = balloon_word_keys or set()
    page_width = page.rect.width
    page_height = page.rect.height
    rotated_line_keys = identify_rotated_lines(page, words)
    line_directions = map_line_directions(page)

    flagged = []
    for w in words:
        x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
        if not text.strip():
            continue
        word_key = (w[5], w[6], w[7]) if len(w) >= 8 else None
        is_balloon_number = word_key is not None and word_key in balloon_word_keys

        # Targeted diagnostic - fires BEFORE any exclusion below, for
        # "ITEM" and any word matching a balloon's own key, so we can see
        # EXACTLY which filter (if any) removes this word from
        # consideration, rather than only seeing words that survived all
        # the way to the crossing test. Confirmed necessary: the previous
        # version of this diagnostic sat AFTER every exclusion check, so a
        # word rejected by an earlier filter never appeared in it at all -
        # invisible failure, indistinguishable from "never considered."
        # Broadened to ANY digit-containing word after is_dimension_like
        # stopped being an exclusion at all: "(730)" (a 3-digit
        # parenthesized dimension) still wasn't flagged, but had zero
        # diagnostic visibility, since the 4+ digit trigger below was
        # calibrated for 6-digit reference numbers specifically and
        # never widened after that exclusion was removed. Now that
        # is_dimension_like no longer drives any behavior, digit count
        # isn't a meaningful filter for what's worth inspecting - any
        # word containing a digit is a candidate for "why wasn't this
        # flagged" and gets full visibility.
        core_text = re.sub(r"[^0-9]", "", text)
        looks_like_reference_number = len(core_text) >= 1
        looks_like_label = text.strip().endswith(":")
        is_target = report_lines is not None and (
            text.strip() == "ITEM" or is_balloon_number or looks_like_reference_number or looks_like_label
        )
        if is_target:
            rect_dbg = fitz.Rect(x0, y0, x1, y1)
            dim_like = is_dimension_like(text)
            punct = is_pure_punctuation(text)
            rotated_like = is_likely_rotated(text, rect_dbg)
            in_rotated_group = len(w) >= 8 and (w[5], w[6]) in rotated_line_keys
            in_exclude_region = any(not (rect_dbg & region).is_empty for region in exclude_regions)
            is_zone_label = len(text.strip()) <= ZONE_LABEL_MAX_CHARS and (
                x0 <= PAGE_EDGE_MARGIN_PT or x1 >= page_width - PAGE_EDGE_MARGIN_PT or
                y0 <= PAGE_EDGE_MARGIN_PT or y1 >= page_height - PAGE_EDGE_MARGIN_PT
            )
            report_lines.append(
                f"    [DEBUG] '{text.strip()}'{' (balloon, word_key=' + str(word_key) + ')' if is_balloon_number else ''} "
                f"at ({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f}): "
                f"is_balloon_number={is_balloon_number} is_dimension_like={dim_like} "
                f"is_pure_punctuation={punct} is_likely_rotated={rotated_like} "
                f"in_rotated_line_group={in_rotated_group} in_exclude_region={in_exclude_region} "
                f"is_zone_label={is_zone_label}"
            )

        if not is_balloon_number and is_pure_punctuation(text):
            # A lone "(" or ")" split off from a bracketed dimension can
            # never itself represent a spelling or content defect, so it's
            # never worth flagging on its own.
            #
            # The is_dimension_like exclusion that used to sit here has
            # been REMOVED, not just narrowed. Unlike every other
            # exclusion in this function, it was never backed by a
            # specific confirmed false positive - just a theoretical
            # assumption ("a dimension value legitimately sits on its own
            # line, that's not a defect"). Directly confirmed on a real
            # drawing that this assumption was wrong in practice: several
            # parenthesized reference dimensions - (75), (730), (1216),
            # (454), (765) - were genuinely crossed by OTHER, unrelated
            # geometry (not their own dimension line), and this exclusion
            # was silently hiding every one of them. Blanket-excluding
            # "text that looks like a dimension" turns out to hide real
            # defects on dimension values just as often as it protects
            # against false ones - the two cases aren't reliably
            # distinguishable from text content alone.
            if is_target:
                report_lines.append("      -> excluded here: is_pure_punctuation")
            continue
        rect = fitz.Rect(x0, y0, x1, y1)
        # is_likely_rotated (an aspect-ratio GUESS at "probably rotated
        # text") and the page-edge zone-label exclusion (a GUESS at
        # "probably a grid-reference letter/number") were removed earlier
        # for the same reason removed here too: in_rotated_line_group -
        # despite being based on a real fact (PyMuPDF's own reported text
        # direction, not a guess) - still turned out to hide genuine
        # defects. Confirmed directly on a real drawing: two SEPARATE
        # dimension values ("2856" and "(730)"), both genuinely crossed
        # by real geometry, were both excluded purely for being part of a
        # rotated text line - being part of a rotated group doesn't mean
        # a word can't ALSO be legitimately crossed by something
        # unrelated. Being evidence-based (as opposed to a guess) turned
        # out not to be the same thing as being safe to blanket-exclude
        # on - the underlying fact was true, but excluding every word
        # sharing that fact was still too broad, the same failure shape
        # as every other heuristic removed today.
        if any(not (rect & region).is_empty for region in exclude_regions):
            if is_target:
                report_lines.append("      -> excluded here: in_exclude_region (BOM table area)")
            continue

        # ── DWG-To-PDF / PDFSHX=2 false-positive filters ──────────────────
        # When AutoCAD exports with DWG To PDF.pc3 + PDFSHX=2 it produces
        # BOTH a hidden searchable text layer AND visible vector outlines of
        # each SHX character.  Three categories of annotation legitimately
        # live inside drawn circles or symbols and must be excluded BEFORE
        # the crossing loop, because the enclosing symbol's own outline
        # always "crosses" through them by design.
        #
        #  1. Balloon numbers  – geometrically confirmed by find_balloon_numbers
        #                        to be inside a callout circle; the circle edge
        #                        always intersects the digit.
        #  2. North-arrow labels (e.g. N1 … N6) – sit inside north-arrow
        #                        symbols; the arrow shaft and surrounding ring
        #                        cross through the letter+digit.
        #  3. Section / detail markers (e.g. 4a, 4b, 4c) – inside section-cut
        #                        or detail-view circles; same geometry.
        if is_balloon_number:
            if is_target:
                report_lines.append(
                    "      -> excluded: balloon number "
                    "(inside its own callout circle, circle edge always crosses digit)"
                )
            continue

        _stripped = text.strip()
        if re.match(r'^N\d+$', _stripped):
            if is_target:
                report_lines.append(
                    f"      -> excluded: north-arrow label '{_stripped}' "
                    f"(inside north-arrow symbol, DWG-To-PDF vector outlines)"
                )
            continue
        if re.match(r'^\d+[a-z]+$', _stripped):
            if is_target:
                report_lines.append(
                    f"      -> excluded: section/detail marker '{_stripped}' "
                    f"(inside section-cut circle, DWG-To-PDF vector outlines)"
                )
            continue

        core = shrink_rect(rect)
        nearby = segments_near_rect(segments, grid, core.x0, core.y0, core.x1, core.y1)

        if is_target:
            report_lines.append(
                f"      survived all exclusions - core=({core.x0:.1f},{core.y0:.1f})-"
                f"({core.x1:.1f},{core.y1:.1f}): {len(nearby)} nearby segment(s):"
            )
            for p1, p2, meta in nearby:
                intersects = segment_intersects_rect(p1, p2, core)
                has_stroke = meta_has_visible_stroke(meta)
                steep = is_steeply_vertical_segment(p1, p2) if intersects else None
                report_lines.append(
                    f"        segment=({p1[0]:.1f},{p1[1]:.1f})-({p2[0]:.1f},{p2[1]:.1f}) "
                    f"intersects_core={intersects} has_visible_stroke={has_stroke} "
                    f"steeply_vertical={steep} type={meta.get('type')!r} "
                    f"stroke_color={meta.get('color')} stroke_opacity={meta.get('stroke_opacity')} "
                    f"width={meta.get('width')}"
                )

        crossing_count = 0
        first_crossing = None
        first_meta = None
        text_angle = text_angle_at(line_directions, rect)
        if is_target:
            report_lines.append(
                f"      text baseline angle: "
                f"{('%.1fdeg' % text_angle) if text_angle is not None else 'NOT FOUND'}"
            )
        for p1, p2, meta in nearby:
            if segment_intersects_rect(p1, p2, core):
                # ── Character-stroke self-intersection filter (PDFSHX=2) ──
                # DWG To PDF.pc3 + PDFSHX=2 keeps the visible vector glyph
                # outlines AND adds a hidden text layer.  A segment whose
                # BOTH endpoints fall within the word's own bounding box
                # (plus tolerance) is that glyph's own stroke, not a foreign
                # line crossing in from outside.  2pt tolerance: catches the
                # dash-dot centreline case where one dash endpoint falls
                # fractionally outside the word box while remaining
                # geometrically part of the label zone.
                #
                # EXCEPTION: only apply this filter for thin strokes
                # (width ≤ 0.36 pt) that are typical of SHX character outlines.
                # A leader line or drawing line that happens to pass entirely
                # through a short word will also have both endpoints inside the
                # bbox but will be noticeably thicker (e.g. 0.50 pt).  We must
                # NOT suppress those — they are real crossings.
                _seg_w = meta.get("width") or 0.0
                _cm = 2.0
                if (_seg_w <= 0.36 and
                        x0 - _cm <= p1[0] <= x1 + _cm and
                        y0 - _cm <= p1[1] <= y1 + _cm and
                        x0 - _cm <= p2[0] <= x1 + _cm and
                        y0 - _cm <= p2[1] <= y1 + _cm):
                    if is_target:
                        report_lines.append(
                            f"      -> skipped: both seg endpoints inside word bbox "
                            f"({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f}) "
                            f"=> own SHX character stroke"
                        )
                    continue
                if not meta_has_visible_stroke(meta):
                    # No visible STROKE - this segment came from a filled
                    # shape's edge, not an actual drawn line. Confirmed on
                    # a real file: a semi-transparent highlight-style
                    # rectangle (stroke_opacity=0.0, fill only, sized to
                    # match the word almost exactly) sat right over a
                    # NOTES word, and its fill-rectangle edges were being
                    # counted as "crossing lines." A highlighter/markup
                    # box behind a word (or any other filled area) is
                    # fundamentally different from a leader/dimension/
                    # table-border LINE actually crossing through it -
                    # only a genuinely stroked path should count here.
                    continue
                if (text_angle is not None and
                        segment_parallel_to_text(p1, p2, text_angle,
                                                 TEXT_BASELINE_PARALLEL_TOLERANCE_DEG)):
                    # The segment runs parallel to this text's own writing
                    # direction. For BLACK (or near-black) strokes this is
                    # almost always the dimension/leader line the text sits
                    # ON, not a foreign line crossing it. Confirmed on a
                    # real drawing: six dimension values on a 35-degree
                    # sloped detail were each flagged by a segment measured
                    # at exactly -35 degrees, i.e. their own dimension line.
                    # Rotated text has a near-square axis-aligned bounding
                    # box (aspect 1.04-1.10 measured), so its own dimension
                    # line passes diagonally through that inflated box even
                    # though nothing visually touches the glyphs.
                    #
                    # COLOURED parallel strokes are a different story.
                    # Centerlines on engineering drawings are conventionally
                    # drawn in a distinct layer colour (commonly magenta
                    # 1,0,1) and often run parallel to dimension text while
                    # cutting straight through it - a real defect. Confirmed
                    # on a real drawing: '(75)' had a magenta centerline
                    # (stroke_color=(1.0, 0.0, 1.0)) through its core that
                    # was being silently skipped by the parallel rule.
                    # Only near-black parallel segments are treated as "own
                    # dimension line"; any clearly coloured parallel stroke
                    # is allowed to flag.
                    stroke_color = meta.get("color")
                    is_near_black = (
                        stroke_color is None
                        or (
                            isinstance(stroke_color, (tuple, list))
                            and len(stroke_color) >= 3
                            and stroke_color[0] <= 0.15
                            and stroke_color[1] <= 0.15
                            and stroke_color[2] <= 0.15
                        )
                    )
                    if is_near_black:
                        if is_target:
                            report_lines.append(
                                f"      -> skipped a segment parallel to the text's own "
                                f"{text_angle:.0f}deg baseline (its own dimension/leader line, "
                                f"near-black stroke)"
                            )
                        continue
                    if is_target:
                        report_lines.append(
                            f"      -> parallel to baseline BUT coloured stroke "
                            f"{stroke_color} - treating as foreign centerline/geometry, not skipping"
                        )
                # The steeply-vertical-centerline exclusion and the
                # crossing-count circuit breaker that used to sit here
                # have both been REMOVED, not just tuned again. Both were
                # heuristic guesses about what a crossing "probably"
                # means, as opposed to the checks that remain (visible
                # stroke, genuine rotation via PyMuPDF's own direction
                # data, the actually-located BOM table region) which are
                # based on real, verifiable facts rather than a guess.
                # Both heuristics kept hiding real defects even after
                # repeated, evidence-based tuning: the vertical-segment
                # exclusion needed a length cap lowered twice after two
                # separate confirmed real crossings slipped through it,
                # and the crossing-count breaker needed raising after two
                # separate words landed at crossing_count=11 in genuinely
                # dense-but-real areas - and even after raising it, a
                # third word landed at 16, one over the new cap. Chasing
                # a "safe" threshold for either one, round after round,
                # wasn't converging - explicit direction was to prioritize
                # catching every real crossing over avoiding overkill
                # highlighting, which these two heuristics were
                # increasingly working against.
                crossing_count += 1
                if first_crossing is None:
                    first_crossing = (p1, p2)
                    first_meta = meta
        if crossing_count > 0:
            flagged.append((text, rect, first_crossing, first_meta))
        if is_target:
            report_lines.append(
                f"      final: crossing_count={crossing_count} "
                f"-> {'FLAGGED' if crossing_count > 0 else 'not flagged'}"
            )
    return flagged


def find_text_overlaps(page, debug_log=None, words=None, exclude_regions=None):
    exclude_regions = exclude_regions or []
    if words is None:
        words = page.get_text("words")
    if len(words) < 2:
        return []

    # Block-level bounding boxes, used below to decide whether two words
    # from different blocks get the more permissive cross-block Y
    # threshold or the standard one. "Different block" alone proved too
    # weak a signal: block structure varies BY PDF PRODUCER for the same
    # visual content. Confirmed directly on one drawing exported two
    # ways: Microsoft Print-to-PDF grouped a title-block disclaimer
    # paragraph as one block (adjacent lines = same-block pairs,
    # correctly held to the stricter threshold), while Inventor's native
    # vector export put each line in its OWN block - instantly turning
    # every ordinary adjacent-line pair into a "cross-block" pair and
    # exploding the text-overlap count from 7 flags to 80, all noise
    # from tightly-spaced small print. The genuine cross-block defect
    # this threshold exists for (an entire note paragraph rendered twice,
    # one copy on top of the other) has a distinguishing structural
    # property: the two BLOCKS are nearly coincident, not just touching
    # at their line boundaries the way adjacent text naturally does.
    block_bboxes = {}
    for w in words:
        if len(w) < 6:
            continue
        bx0, by0, bx1, by1, bno = w[0], w[1], w[2], w[3], w[5]
        if bno not in block_bboxes:
            block_bboxes[bno] = [bx0, by0, bx1, by1]
        else:
            bb = block_bboxes[bno]
            bb[0] = min(bb[0], bx0); bb[1] = min(bb[1], by0)
            bb[2] = max(bb[2], bx1); bb[3] = max(bb[3], by1)

    def blocks_substantially_overlap(bno1, bno2):
        bb1 = block_bboxes.get(bno1)
        bb2 = block_bboxes.get(bno2)
        if bb1 is None or bb2 is None:
            return False
        ix0, iy0 = max(bb1[0], bb2[0]), max(bb1[1], bb2[1])
        ix1, iy1 = min(bb1[2], bb2[2]), min(bb1[3], bb2[3])
        if ix1 <= ix0 or iy1 <= iy0:
            return False
        inter_area = (ix1 - ix0) * (iy1 - iy0)
        area1 = (bb1[2] - bb1[0]) * (bb1[3] - bb1[1])
        area2 = (bb2[2] - bb2[0]) * (bb2[3] - bb2[1])
        smaller = min(area1, area2)
        if smaller <= 0:
            return False
        return (inter_area / smaller) >= CROSS_BLOCK_MIN_BLOCK_OVERLAP_FRACTION

    boxes = []
    for w in words:
        x0, y0, x1, y1, text, block_no, line_no = w[0], w[1], w[2], w[3], w[4], w[5], w[6]
        text = text.strip()
        if len(text) < TEXT_OVERLAP_MIN_CHARS:
            continue
        # Skip entirely lowercase words - confirmed on a real drawing that
        # title-block disclaimer/caution text (all lowercase prose) was
        # producing dozens of false-positive overlap flags. Engineering
        # drawing content that genuinely matters for overlap checking
        # (labels, notes, dimensions, reference numbers) is always
        # uppercase or mixed-case with uppercase first letter. A word
        # that's entirely lowercase is almost certainly flowing prose
        # (the CAUTION box, disclaimer text, drawing number suffixes)
        # where adjacent lines are supposed to be close together.
        if text == text.lower() and text.isalpha():
            continue
        # Skip known drawing annotation label words - these are structural
        # labels (SECTION, DETAIL, SCALE, VIEW, ITEM, NOTE, NOTES) that
        # always appear near other text as part of a composed annotation
        # (e.g. "SECTION A  SCALE 1:5"). They are never a genuine overlap
        # defect and generate false positives when adjacent blocks overlap.
        if text in {"SECTION", "DETAIL", "SCALE", "VIEW", "NOTE", "NOTES", "ITEM"}:
            continue
        # Skip any purely alphabetic word (letters only, no digits) - genuine
        # overlap defects always involve numbers or reference codes. Two pure-
        # letter words in adjacent annotation lines (e.g. "OMITTED" vs
        # "PLACES)") are never a real drawing defect.
        if re.fullmatch(r"[A-Za-z()]+", text):
            continue
        r = fitz.Rect(x0, y0, x1, y1)
        if any(not (r & region).is_empty for region in exclude_regions):
            continue
        # Skip words whose bounding box is taller than wide (aspect > 1.5)
        # - confirmed on a real drawing: "FLOW" and "DIRECTION" are a
        # vertical text label where each word sits in its own block (the
        # PDF's own structure), so the same-block exclusion doesn't apply.
        # But vertically-stacked label words are by convention always
        # deliberately adjacent - they can't be a "two objects accidentally
        # overlapping" defect. Their bboxes have height >> width because
        # the text is rotated, producing y_overlap=1.0 that triggers the
        # check inappropriately.
        w_ = r.x1 - r.x0
        h_ = r.y1 - r.y0
        if h_ > 0 and w_ > 0 and (h_ / w_) > 1.5:
            continue
        # Skip hyphenated reference codes (drawing numbers, part numbers,
        # document references like "PP00008-GTA-3230-8-000001") - confirmed
        # on a real drawing these were being matched against adjacent
        # title-block label words ("DRAWING", "NUMBER") that naturally sit
        # on the same Y band. A genuine duplicate-text defect involves
        # plain words or phrases overlapping; a hyphenated reference code
        # is always a structured value field in a title block, never the
        # source of an accidental overlap defect. Requires BOTH a hyphen
        # AND at least one digit to avoid skipping ordinary hyphenated
        # words like "SELF-SUPPORTING".
        if '-' in text and any(c.isdigit() for c in text):
            continue
        boxes.append((r, text, block_no, line_no))

    flagged = []
    flagged_pairs = set()
    for i in range(len(boxes)):
        r1, t1, b1, l1 = boxes[i]
        w1 = r1.x1 - r1.x0
        h1 = r1.y1 - r1.y0
        if w1 <= 0 or h1 <= 0:
            continue
        for j in range(i + 1, len(boxes)):
            r2, t2, b2, l2 = boxes[j]
            if b1 == b2:
                # Same text block - words within one block are by definition
                # flowing content (consecutive words on a line, or consecutive
                # lines in a paragraph/label). Their bboxes naturally touch
                # or overlap for ordinary reasons: line spacing in rotated
                # vertical text, tight leading, justified text. Confirmed on
                # a real drawing: "FLOW" and "DIRECTION" (consecutive lines
                # of a vertical label, same block) were being flagged purely
                # because their Y overlap exceeded the threshold when the
                # text is rotated. Same-block pairs can never be a genuine
                # "different text objects overlapping" defect.
                continue
            if t1 == t2:
                # Only skip if ALSO at (near) IDENTICAL position - some
                # title blocks simulate bold by drawing every character
                # twice at the EXACT same position rather than using a
                # real bold font. Confirmed on a real drawing: every
                # character of "PROJECT", "CLIENT" etc. had two glyphs at
                # identical x0/x1 coordinates, not even a tiny offset.
                # Narrowed after a SECOND confirmed case on a different
                # drawing: two separate "187" dimension values, genuinely
                # ~14pt apart, were being silently skipped just for
                # having the same text - hiding a real overlap the user
                # directly confirmed. Same text at a meaningfully
                # different position is a completely different situation
                # and should still go through the normal overlap check
                # below, same as any other pair of words.
                if (abs(r1.x0 - r2.x0) < FAKE_BOLD_POSITION_TOLERANCE_PT and
                        abs(r1.y0 - r2.y0) < FAKE_BOLD_POSITION_TOLERANCE_PT):
                    continue
            w2 = r2.x1 - r2.x0
            h2 = r2.y1 - r2.y0
            if w2 <= 0 or h2 <= 0:
                continue
            inter = r1 & r2
            if inter.is_empty:
                continue
            inter_w = inter.x1 - inter.x0
            inter_h = inter.y1 - inter.y0
            x_frac = inter_w / min(w1, w2)
            y_frac = inter_h / min(h1, h2)
            # A lower Y bar applies when the two words come from genuinely
            # DIFFERENT text blocks whose block-level areas SUBSTANTIALLY
            # overlap - the signature of an entire block rendered on top
            # of another (a duplicate note paragraph, confirmed real).
            # "Different block" ALONE proved producer-dependent and too
            # weak - see blocks_substantially_overlap above for the
            # confirmed case where one exporter's per-line block
            # structure turned every ordinary adjacent line into a
            # "cross-block" pair, exploding 7 flags into 80. Requiring
            # the BLOCKS themselves to be substantially coincident (not
            # just edge-touching, which is what normal adjacent text
            # does) keeps catching the genuine duplicate-overlay case
            # regardless of exporter, without inheriting the exporter's
            # arbitrary block-splitting decisions as a defect signal.
            cross_block_overlay = (b1 != b2) and blocks_substantially_overlap(b1, b2)
            # Don't apply the permissive cross-block threshold if either
            # word is a hyphenated string - confirmed on a real drawing:
            # "DRAWING" and "NUMBER" (title-block label words) were being
            # matched against "PP00008-GTA-3230-8-000001" (the drawing
            # number value) via cross_block_overlay=True because both
            # blocks sit in the same title-block corner area. A duplicate-
            # paragraph overlay defect (the intended target of this
            # threshold) involves repeated PLAIN TEXT words, never
            # hyphenated reference codes. Drawing numbers, part numbers,
            # and document references always contain hyphens; duplicate
            # overlapping notes never do.
            if '-' in t1 or '-' in t2:
                cross_block_overlay = False
            y_needed = TEXT_OVERLAP_Y_FRACTION_CROSS_BLOCK if cross_block_overlay else TEXT_OVERLAP_Y_FRACTION
            is_flagged = x_frac >= TEXT_OVERLAP_X_FRACTION and y_frac >= y_needed
            if debug_log is not None and not is_flagged and x_frac >= 0.15 and y_frac >= 0.15:
                # Near-miss visibility: confirmed necessary on a real
                # drawing - two stacked dimension values ("2360" over
                # "(3284) O/A") looked visually overlapping in a
                # screenshot but weren't flagged by EITHER this check or
                # an independent, filter-free test script using the same
                # threshold - meaning their boxes genuinely don't clear
                # 60%/60%, not that some exclusion is hiding them. Logging
                # every MEANINGFULLY-overlapping pair (not just any
                # incidental corner touch from normal text kerning, which
                # would otherwise flood the report) shows the real numbers
                # instead of guessing whether the threshold needs loosening.
                debug_log.append(
                    f"    text overlap near-miss: '{t1}' vs '{t2}' near "
                    f"({r1.x0:.1f},{r1.y0:.1f}): x_overlap={x_frac:.2f}, "
                    f"y_overlap={y_frac:.2f} (need >= {TEXT_OVERLAP_X_FRACTION}/"
                    f"{y_needed} [{'overlay-cross-block' if cross_block_overlay else 'standard'}]) -> not flagged "
                    f"[block1={b1} line1={l1} block2={b2} line2={l2}]"
                )
            if is_flagged:
                key = (i, j)
                if key not in flagged_pairs:
                    flagged_pairs.add(key)
                    if debug_log is not None:
                        debug_log.append(
                            f"    text overlap FLAGGED: '{t1}' vs '{t2}' near "
                            f"({r1.x0:.1f},{r1.y0:.1f}): x_overlap={x_frac:.2f}, "
                            f"y_overlap={y_frac:.2f} threshold={y_needed} "
                            f"cross_block_overlay={cross_block_overlay} "
                            f"[block1={b1} line1={l1} block2={b2} line2={l2}]"
                        )
                    flagged.append((r1, t1, r2, t2))
    return flagged


def _has_diagonal_segment(segment_list):
    """True if ANY segment in the list is meaningfully off-axis (not
    within BALLOON_AXIS_TOLERANCE_DEG of 0 or 90 degrees).

    Shared by both the wide-search-fallback acceptance decision and the
    final balloon accept/reject gate in find_balloon_circles, so both use
    identical, independently-verified logic rather than two separate
    inline implementations that could drift apart.

    Deliberately doesn't care whether the diagonal comes from a true
    bezier 'c' segment or an 'l' segment - confirmed on a real drawing
    that a genuine circular balloon was drawn using 59 short STRAIGHT
    lines approximating the circle, never a true curve command, and 55 of
    those 59 were still clearly diagonal (10-85 degrees). Requiring a
    true curve command in addition to this check rejected that balloon
    outright; orientation alone is the correct and sufficient signal.
    """
    for p1, p2, meta in segment_list:
        dx, dy = abs(p2[0] - p1[0]), abs(p2[1] - p1[1])
        if dx < 1e-6 and dy < 1e-6:
            continue
        angle = math.degrees(math.atan2(dy, dx))
        if BALLOON_AXIS_TOLERANCE_DEG < angle < 90 - BALLOON_AXIS_TOLERANCE_DEG:
            return True
    return False


def find_balloon_circles(page, segments, grid, debug_log=None, words=None, bom_regions=None):
    """Identifies balloon reference numbers - a short (1-3 digit) number
    with SOME meaningful geometry drawn around/near it, as opposed to an
    isolated digit with nothing nearby (a grid reference, a BOM quantity
    sitting in a plain table cell).

    Deliberately does NOT use precise shape (aspect ratio, diameter) to
    decide whether something IS a balloon anymore. That approach required
    correctly reconstructing an accurate outline from the underlying
    line/curve segments just to answer a yes/no question, and proved
    fragile in a way that kept resurfacing under different names -
    sensitive to whether a circle happened to be drawn with curves or
    straight lines, to exactly how many segments a search box's edge
    happened to clip, and to unrelated precision improvements made
    elsewhere in the tool. The accept/reject decision below is purely a
    segment-count threshold now - a low bar that just distinguishes
    "there's clearly something drawn here" from genuinely isolated text.

    The RECT (used for balloon-vs-balloon overlap and for locating the
    balloon) is a different matter - it still uses the real measured
    extent from the same nearby segments already gathered for the
    accept/reject count, since that data is sitting right there and a
    fixed guess turned out to be measurably wrong on a real drawing: two
    balloons (front position ~15pt apart) visually overlapping by a
    clearly significant amount only produced ~1pt of overlap using a
    fixed 5pt padding guess, nowhere near the flagging threshold. Falls
    back to the fixed-padding estimate only if the measured extent comes
    back degenerate (zero-size) - the accept/reject decision itself never
    depends on this measurement either way, so a degenerate measurement
    here can't cause a real balloon to go unrecognized, only make its
    rect a little less precise for overlap purposes specifically.

    Also flags "overlaps_geometry" - whether this balloon's own outline
    genuinely overlaps unrelated drawing detail (as opposed to a line
    crossing the TEXT, which find_line_crossings already handles
    separately). Confirmed on a real drawing via raw geometry dump: a
    balloon's own outline was drawn entirely in one color (magenta) while
    the surrounding drawing detail it visually overlapped was a
    DIFFERENT color (black) - the balloon's own segments dominate the
    color count within its own tight search box, so any meaningfully-
    present OTHER color within the balloon's final measured rect is a
    reliable signal of genuine overlap with unrelated geometry, without
    needing to hard-code which color balloons happen to use on any given
    drawing (confirmed elsewhere in this same tool's development that
    balloons are drawn in plain black just as often).

    Returns list of dicts: rect, center, radius, text, word_key,
    overlaps_geometry, foreign_segment_count.
    """
    if words is None:
        words = page.get_text("words")
    if not segments:
        return []

    candidates = []
    for w in words:
        x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
        text = text.strip()
        if not re.fullmatch(r"\d{1,3}", text):
            continue

        # Exclude numbers that sit inside the BOM table - the ITEM column
        # numbers (1, 2, 3 ...) are plain table text, not balloon circles.
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if bom_regions and any(r.contains(fitz.Point(cx, cy)) for r in bom_regions):
            continue

        # Exclude numbers within the page border margin - these are sheet
        # grid reference labels (1,2,3...12 along top/bottom, A-H along
        # sides) and are never balloon callouts.
        page_width  = page.rect.width
        page_height = page.rect.height
        if (x0 <= PAGE_EDGE_MARGIN_PT or x1 >= page_width - PAGE_EDGE_MARGIN_PT or
                y0 <= PAGE_EDGE_MARGIN_PT or y1 >= page_height - PAGE_EDGE_MARGIN_PT):
            continue

        # Exclude digits that are part of a scale ratio (e.g. "1" and "10"
        # in "SCALE 1 : 10"). The colon is its own word token; if any word
        # in the same text block is ":" within 40pt horizontally, this is
        # a ratio component, not a balloon number.
        block_no = w[5] if len(w) >= 6 else None
        if block_no is not None:
            is_scale_ratio = any(
                ww[4].strip() == ":"
                and ww[5] == block_no
                and abs((ww[0] + ww[2]) / 2 - cx) <= 40.0
                for ww in words
            )
            if is_scale_ratio:
                continue

        def gather(rx0, ry0, rx1, ry1):
            broad_ = segments_near_rect(segments, grid, rx0, ry0, rx1, ry1)
            nearby_count_ = 0
            kinds_ = {}
            xs_, ys_ = [], []
            color_counts_ = {}
            filtered_ = []  # segments that actually passed the midpoint test
            for p1, p2, meta in broad_:
                mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                if rx0 <= mx <= rx1 and ry0 <= my <= ry1:
                    nearby_count_ += 1
                    k = meta.get("src_kind", "?")
                    kinds_[k] = kinds_.get(k, 0) + 1
                    xs_.append(p1[0]); xs_.append(p2[0])
                    ys_.append(p1[1]); ys_.append(p2[1])
                    color = meta.get("color")
                    color_counts_[color] = color_counts_.get(color, 0) + 1
                    filtered_.append((p1, p2, meta))
            return filtered_, nearby_count_, kinds_, xs_, ys_, color_counts_

        rx0, rx1 = x0 - BALLOON_SEARCH_MARGIN, x1 + BALLOON_SEARCH_MARGIN
        ry0, ry1 = y0 - BALLOON_SEARCH_MARGIN, y1 + BALLOON_SEARCH_MARGIN
        nearby, nearby_count, kinds, xs, ys, color_counts = gather(rx0, ry0, rx1, ry1)
        used_tall_search = False

        # A balloon can be a multi-line oval (an item number stacked
        # directly over its own reference number, both inside one shape) -
        # the normal narrow search only reaches around ONE line, so it can
        # come back nearly empty even for a genuine balloon. Confirmed on
        # MULTIPLE separate real drawings, several balloons each time. A
        # PRIOR fix for this (grouping by the PDF's own internal "block"
        # number) was tried and reverted after it caused a severe
        # regression - a PDF block can span far more than just two
        # adjacent lines, sweeping in unrelated content and exploding
        # false-positive counts (182 flags where ~25 was normal). This is
        # deliberately much narrower and safer: only triggers as a SECOND
        # attempt when the normal search already failed (so it can never
        # change behavior for anything that already works). Both X and Y
        # margins are widened together, each sized from real measured
        # data rather than a guess - see the constants above for the raw
        # geometry dump that quantified both.
        if nearby_count < BALLOON_MIN_SEGMENTS:
            rx0_wide = x0 - BALLOON_TALL_SEARCH_MARGIN_X_PT
            rx1_wide = x1 + BALLOON_TALL_SEARCH_MARGIN_X_PT
            ry0_wide = y0 - BALLOON_TALL_SEARCH_MARGIN_Y_PT
            ry1_wide = y1 + BALLOON_TALL_SEARCH_MARGIN_Y_PT
            nearby2, nearby_count2, kinds2, xs2, ys2, color_counts2 = gather(rx0_wide, ry0_wide, rx1_wide, ry1_wide)
            # Only accept the wide result if it contains genuinely
            # diagonal geometry (not just more axis-aligned clutter) -
            # confirmed on real geometry dumps that genuine oval/circular
            # balloon shapes always have SOME non-axis-aligned segments
            # (whether drawn with true curve commands or many short
            # straight-line segments approximating a curve), while every
            # confirmed rogue case from batch testing was purely axis-
            # aligned (BOM row numbers, table borders, dimension lines).
            # A wider search that finds only axis-aligned lines found
            # incidental drafting-convention geometry, not a real balloon.
            wide_has_diagonal = _has_diagonal_segment(nearby2)
            if nearby_count2 > nearby_count and wide_has_diagonal:
                nearby, nearby_count, kinds, xs, ys, color_counts = nearby2, nearby_count2, kinds2, xs2, ys2, color_counts2
                rx0, rx1, ry0, ry1 = rx0_wide, rx1_wide, ry0_wide, ry1_wide
                used_tall_search = True

        accepted = nearby_count >= BALLOON_MIN_SEGMENTS

        # Require at least one curve segment ('c' kind) - genuine balloon
        # shapes (circles, ovals) must have curves. Confirmed on a real
        # drawing: candidates with {'l': 44} (pure line segments, all
        # straight) were being ACCEPTED because the orientation check
        # below found one slightly-angled arrow-head or tick segment among
        # the 44 lines, defeating that check. Requiring curves is a
        # stronger, more direct signal: a curved enclosing shape MUST
        # have curve segments; dimension lines, BOM borders, and arrow
        # heads are all straight 'l' segments, never 'c'.
        # NOTE: a prior version also required at least one true bezier
        # 'c'-kind segment here, on top of the orientation check below.
        # Removed after a confirmed real case: a genuine circular balloon
        # (digits '1'/'2' on a real drawing) was drawn using 59 short
        # STRAIGHT-LINE segments approximating the circle - never a true
        # curve command - exactly like an earlier confirmed balloon ('15')
        # much earlier in this tool's development. The 'c'-kind
        # requirement rejected it outright, before the orientation check
        # even ran, and the debug output then misleadingly reported "all
        # segments axis-aligned" as the reason (a different check
        # entirely) since the generic status message didn't distinguish
        # between the two gates. Manually re-checked the actual segment
        # angles for that case: 55 of 59 were genuinely diagonal (10-85
        # degrees), confirming the orientation check alone was already
        # correct and sufficient - it doesn't matter whether a curve is
        # drawn with one bezier command or a hundred straight segments
        # approximating it, only whether the geometry is genuinely
        # non-axis-aligned. The orientation check below already handles
        # both drawing conventions correctly and remains the sole gate.

        # The "surrounds on all 4 sides" check this replaced was tried
        # and found insufficient: verified fine against a NARROW
        # geometry sample, but the actual production wide-search box
        # (35pt/20pt margins) turned out to sweep in just enough
        # incidental geometry on every side to satisfy it even for a
        # confirmed non-balloon case - two dimension-line/arrow segments
        # sitting right next to the "413" digit's own edge were enough
        # to add a 4th "side," even though they're not an enclosing
        # shape at all. A wider net can accidentally touch every
        # direction in a busy area; presence alone isn't discriminating
        # enough.
        #
        # Segment ORIENTATION is a stronger signal, verified against the
        # same two real cases: dimension/extension/centerline geometry in
        # a CAD drawing is essentially always purely horizontal or
        # vertical (0/90 degrees) by strict professional convention - a
        # confirmed real case ("413") had ALL nearby segments at exactly
        # 0 or 90 degrees, nothing else. A genuine curved enclosing shape
        # (circle/oval) can't be purely axis-aligned - its tangent
        # direction continuously changes - a confirmed real oval balloon
        # had segments at four distinct angles (0/45/90/135). Requiring
        # at least one meaningfully non-axis-aligned segment is a much
        # harder thing for orthogonal drafting-convention clutter to
        # satisfy by accident, no matter how wide the search net is.
        has_diagonal = None
        if accepted:
            has_diagonal = _has_diagonal_segment(nearby)
            if not has_diagonal:
                accepted = False

        if debug_log is not None:
            if accepted:
                status = "ACCEPTED"
            elif nearby_count < BALLOON_MIN_SEGMENTS:
                status = f"rejected (need >= {BALLOON_MIN_SEGMENTS})"
            else:
                status = "rejected (all segments axis-aligned - see below)"
            tall_note = " [used wider multi-line search]" if used_tall_search else ""
            debug_log.append(
                f"    candidate '{text}' at ({x0:.1f},{y0:.1f}): "
                f"{nearby_count} nearby segment(s)  -> {status} [kinds: {kinds}]{tall_note}"
            )
            if has_diagonal is False:
                debug_log.append(
                    "      -> every nearby segment is purely horizontal/vertical - "
                    "looks like dimension/extension-line clutter, not a curved "
                    "enclosing shape"
                )

        if accepted:
            # Prefer the geometry bbox from nearby curve/line segments when
            # we have real outline points. Word-based rect (text + padding)
            # was used for multi-line ovals and systematically UNDER-sized
            # the true oval - confirmed: balloons 1 & 2 on a dual-oval
            # drawing measured 49.8pt wide with a 14pt gap between rects
            # while the drawn outlines clearly crossed. Segment endpoints
            # (xs/ys) track the actual path and catch that overlap.
            measured_w = max(xs) - min(xs) if xs else 0
            measured_h = max(ys) - min(ys) if ys else 0
            geo_rect = None
            if measured_w > 0 and measured_h > 0 and nearby_count >= BALLOON_MIN_SEGMENTS:
                geo_rect = fitz.Rect(min(xs), min(ys), max(xs), max(ys))

            if used_tall_search:
                # Word-based estimate still useful as a FALLBACK when
                # geometry is sparse. Keep the same block/line filters so
                # adjacent balloons sharing a PDF block do not get identical
                # rects (prior regression: false 3/4 overlap).
                block_no = w[5] if len(w) >= 6 else None
                bx0, by0, bx1, by1 = x0, y0, x1, y1
                if block_no is not None and words:
                    for ww in words:
                        if len(ww) < 6 or ww[5] != block_no:
                            continue
                        if ww[1] > y1 + BALLOON_TALL_SEARCH_MARGIN_Y_PT:
                            continue
                        if ww[3] < y0 - BALLOON_TALL_SEARCH_MARGIN_Y_PT:
                            continue
                        ww_text = ww[4].strip() if len(ww) >= 5 else ''
                        if ww_text != text and re.fullmatch(r'\d{1,3}', ww_text):
                            continue
                        if re.fullmatch(r'[A-Za-z:\.]+', ww_text):
                            continue
                        bx0 = min(bx0, ww[0])
                        by0 = min(by0, ww[1])
                        bx1 = max(bx1, ww[2])
                        by1 = max(by1, ww[3])
                word_rect = fitz.Rect(
                    bx0 - BALLOON_ASSUMED_PADDING_PT,
                    by0 - BALLOON_ASSUMED_PADDING_PT,
                    bx1 + BALLOON_ASSUMED_PADDING_PT,
                    by1 + BALLOON_ASSUMED_PADDING_PT,
                )
                # Geometry wins when it is at least as large as the word
                # estimate in both axes (true oval outline). Otherwise keep
                # the word rect so multi-line text still expands the box.
                if geo_rect is not None and (
                        geo_rect.width >= word_rect.width * 0.9 and
                        geo_rect.height >= word_rect.height * 0.9):
                    rect = geo_rect
                else:
                    # Union the two so we never shrink below either estimate
                    if geo_rect is not None:
                        rect = fitz.Rect(
                            min(geo_rect.x0, word_rect.x0),
                            min(geo_rect.y0, word_rect.y0),
                            max(geo_rect.x1, word_rect.x1),
                            max(geo_rect.y1, word_rect.y1),
                        )
                    else:
                        rect = word_rect
            else:
                if geo_rect is not None:
                    rect = geo_rect
                else:
                    rect = fitz.Rect(
                        x0 - BALLOON_ASSUMED_PADDING_PT, y0 - BALLOON_ASSUMED_PADDING_PT,
                        x1 + BALLOON_ASSUMED_PADDING_PT, y1 + BALLOON_ASSUMED_PADDING_PT,
                    )
            cx, cy = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
            radius = ((rect.x1 - rect.x0) + (rect.y1 - rect.y0)) / 4

            if debug_log is not None:
                debug_log.append(
                    f"      -> measured rect: ({rect.x0:.1f},{rect.y0:.1f})-"
                    f"({rect.x1:.1f},{rect.y1:.1f})  (w={rect.x1-rect.x0:.1f} h={rect.y1-rect.y0:.1f})"
                )

            # Foreign geometry inside the balloon outline.
            # Path A (colour): other stroke colour than the balloon's own
            # dominant outline colour - works when balloons are on a coloured
            # layer.
            # Path B (spatial, monotone): on printed mono drawings balloon
            # and part geometry share black, so colour cannot separate them.
            # Own outline segments sit near radius r from centre; foreign
            # geometry that clashes (flange circles, panel edges) has
            # endpoints well outside the balloon while still cutting the
            # interior core.
            dominant_color = max(color_counts, key=color_counts.get) if color_counts else None
            foreign_segments = []
            r_eff = max(radius, 1.0)
            core = fitz.Rect(
                rect.x0 + rect.width * 0.22,
                rect.y0 + rect.height * 0.22,
                rect.x1 - rect.width * 0.22,
                rect.y1 - rect.height * 0.22,
            )
            # Skip geometry-overlap scan for circles too large to be BOM
            # balloons (mechanical bores, flanges, etc.).
            _skip_overlap = radius > BALLOON_MAX_GEOMETRY_OVERLAP_RADIUS_PT
            for p1, p2, meta in ([] if _skip_overlap else nearby):
                mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                # Use circular boundary (not rectangular) so neighbouring
                # balloon arcs that only touch the rect corner—but are
                # outside the actual circle—are not counted as "inside".
                inside_circle = (mx - cx) ** 2 + (my - cy) ** 2 < r_eff ** 2
                if not inside_circle:
                    # Still count segments that cross the core even if midpoint
                    # is outside (long chords through the balloon).
                    crosses_core = segments_intersect(
                        p1, p2,
                        (core.x0, core.y0), (core.x1, core.y0)
                    ) or segments_intersect(
                        p1, p2,
                        (core.x0, core.y1), (core.x1, core.y1)
                    ) or segments_intersect(
                        p1, p2,
                        (core.x0, core.y0), (core.x0, core.y1)
                    ) or segments_intersect(
                        p1, p2,
                        (core.x1, core.y0), (core.x1, core.y1)
                    ) or (core.x0 <= mx <= core.x1 and core.y0 <= my <= core.y1)
                    if not crosses_core:
                        continue
                d1 = ((p1[0] - cx) ** 2 + (p1[1] - cy) ** 2) ** 0.5
                d2 = ((p2[0] - cx) ** 2 + (p2[1] - cy) ** 2) ** 0.5
                color_foreign = (
                    dominant_color is not None
                    and meta.get("color") is not None
                    and meta.get("color") != dominant_color
                )
                # Spatial foreign: segment reaches from well outside the
                # outline into (or across) the balloon core.
                spatial_foreign = (
                    max(d1, d2) > r_eff * 1.25
                    and min(d1, d2) < r_eff * 1.05
                )
                if color_foreign or spatial_foreign:
                    foreign_segments.append((p1, p2, meta))
            overlaps_geometry = (
                not _skip_overlap
                and len(foreign_segments) >= BALLOON_FOREIGN_SEGMENT_MIN
            )

            if debug_log is not None and overlaps_geometry:
                debug_log.append(
                    f"      -> ALSO overlaps {len(foreign_segments)} foreign "
                    f"segment(s) within outline (dominant color: {dominant_color})"
                )

            candidates.append({
                "rect": rect, "center": (cx, cy), "radius": radius, "text": text,
                "overlaps_geometry": overlaps_geometry,
                "foreign_segment_count": len(foreign_segments),
                "tall_search": used_tall_search,
                # A stable identity key for the word this balloon number
                # came from - used by find_line_crossings to recognize this
                # specific word as a balloon number rather than a plain
                # dimension value (see the comment there). Uses the word's
                # own (block_no, line_no, word_no) integers rather than its
                # rounded coordinates - confirmed on a real drawing that
                # rounded-float matching silently failed for one specific
                # balloon (a genuine, confirmed crossing at "8" never even
                # reached the line-crossing diagnostic, meaning the match
                # failed before that point) while working for others on the
                # same page. Integer block/line/word numbers can't have a
                # floating-point rounding mismatch the way coordinates can.
                "word_key": (w[5], w[6], w[7]) if len(w) >= 8 else None,
            })

    # Deduplicate: multiple word tokens from the same physical balloon region
    # can each pass the segment test and get appended as separate candidates
    # with identical or near-identical centre coordinates. This produces
    # dist=0.0 in the overlap check (same centre vs same centre), flagging
    # every such pair as overlapping. Keep only the first candidate within
    # 1pt of any earlier one — BUT only when they carry the same text.
    #
    # Critical: in a stacked balloon group (e.g. "6 7 8" in a row), the
    # "wider multi-line search" computes each balloon's measured rect from
    # ALL nearby segments in the group area, so every balloon's rect covers
    # roughly the same large span and their derived centres land within ~1pt
    # of each other. Without the text-equality guard, "7" and "8" would dedup
    # against each other (both genuine, different item numbers), leaving "8"
    # absent from balloon_numbers and falsely triggering a BOM-no-balloon flag.
    # Two candidates with DIFFERENT text values are always different physical
    # balloons — never suppress one.
    DEDUP_DIST_PT = 1.0
    deduped = []
    for cand in candidates:
        cx, cy = cand["center"]
        cand_text = cand["text"].strip()
        if not any(
            d["text"].strip() == cand_text and
            ((cx - d["center"][0]) ** 2 + (cy - d["center"][1]) ** 2) ** 0.5 < DEDUP_DIST_PT
            for d in deduped
        ):
            deduped.append(cand)
    return deduped



# BALLOON_OVERLAP_X_FRACTION / BALLOON_OVERLAP_Y_FRACTION / BALLOON_OVERLAP_EXPAND_PT
# - all retired. Replaced by a pure center-distance check (BALLOON_PROXIMITY_THRESHOLD_PT)
# that doesn't require accurately measuring the balloon's shape boundary. See
# find_balloon_overlaps for the confirmed data points that calibrated the threshold.
BALLOON_PROXIMITY_THRESHOLD_PT = 80.0

# Known real-world balloon sizes, in mm as measured off the actual drafting
# standard, converted to PDF points (1mm = 2.834645669pt at the standard
# 72pt/inch PDF unit). Using a KNOWN size rather than estimating one from
# segments is a fundamentally different approach from every balloon/circle
# check tried before this - there is no clustering, no radius guess, no
# shape reconstruction, so none of their failure modes (fragmented circles,
# balloons matched against themselves, wildly inflated rects) can occur
# here. The only inputs are a digit's own text-box centre (always reliable)
# and a fixed number supplied directly by the drawing office.
MM_TO_PT = 2.834645669
# 5.25mm was originally supplied and treated as a RADIUS - corrected after
# real measured data disagreed. Confirmed on a real drawing: adjacent
# balloons "5"/"6" and "6"/"7", visually just touching (not crossing),
# measured a centre-to-centre gap of ~14.9-15.0pt. For two tangent circles
# that gap equals r1+r2 exactly, so each circle's real radius is ~7.4-
# 7.5pt (~2.6mm) - i.e. 5.25mm is the DIAMETER, not the radius (2 x
# 2.625mm = 5.25mm matches the measured gap almost exactly). Treating it
# as a radius had silently doubled the true circle size.
BOM_BALLOON_DIAMETER_MM = 5.25
BOM_BALLOON_RADIUS_MM = BOM_BALLOON_DIAMETER_MM / 2
BOM_BALLOON_RADIUS_PT = BOM_BALLOON_RADIUS_MM * MM_TO_PT
# Small tolerance so two balloons whose edges are drawn exactly tangent
# (touching, not crossing - a normal, deliberate drafting convention for
# grouped references) don't flag purely from floating-point/measurement
# noise at the boundary.
KNOWN_SIZE_OVERLAP_TOLERANCE_PT = 3.0  # forgives tangent/touching balloons (dist≈2r); only flags genuine overlaps


def find_balloon_overlaps_known_size(balloons, debug_log=None):
    """Flags pairs of STANDARD BOM CIRCLE balloons whose known real-world
    radius means they must be genuinely overlapping, using an exact
    geometric test rather than an estimate.

    dist(center1, center2) < r1 + r2  =>  the two circles overlap.
    dist(center1, center2) == r1 + r2  =>  the two circles are exactly
        tangent (touching, not crossing) - NOT flagged, per the drawing
        office's own convention that grouped balloons are often placed
        touching.
    dist(center1, center2) > r1 + r2  =>  clear.

    This only covers the standard BOM circle balloon for now
    (BOM_BALLOON_RADIUS_PT, 5.25mm radius as supplied directly). Other
    balloon shapes (oval ITEM/SECTION labels, hexagon callouts) are a
    different, larger size and are NOT yet covered by this function -
    they still go through the disabled estimation-based checks, or
    nothing at all, until their real sizes are supplied the same way.
    """
    flagged = []
    r = BOM_BALLOON_RADIUS_PT
    for i in range(len(balloons)):
        cx1, cy1 = balloons[i]["center"]
        for j in range(i + 1, len(balloons)):
            # Skip pairs where either balloon used the tall-search path -
            # those are oval callouts (stacked number + reference code) whose
            # computed centre is unreliable for distance checks. The known-
            # size radius is calibrated for standard circle balloons only.
            if balloons[i].get("tall_search") or balloons[j].get("tall_search"):
                continue
            cx2, cy2 = balloons[j]["center"]
            dist = ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5
            threshold = 2 * r - KNOWN_SIZE_OVERLAP_TOLERANCE_PT
            is_flagged = dist < threshold
            if debug_log is not None:
                debug_log.append(
                    f"    balloon '{balloons[i]['text']}' at ({cx1:.1f},{cy1:.1f}) vs "
                    f"'{balloons[j]['text']}' at ({cx2:.1f},{cy2:.1f}): "
                    f"center dist={dist:.1f}pt, known r1+r2={2*r:.1f}pt "
                    f"-> {'FLAGGED' if is_flagged else 'not flagged'}"
                )
            if is_flagged:
                flagged.append((balloons[i], balloons[j]))
    return flagged


def find_balloon_overlaps(balloons, debug_log=None):
    """Flags pairs of item-reference balloons that are too close together,
    indicating their enclosing shapes are overlapping regardless of whether
    that shape is a circle, oval, hexagon, or anything else.

    APPROACH CHANGE: replaced the rect-intersection approach (which required
    accurately measuring the balloon shape boundary, repeatedly fragile
    across different PDF exporters and shape types) with a pure
    center-to-center distance check. The only question is: are these two
    balloon digits physically close enough that whatever shape encloses them
    is likely overlapping the other? Shape doesn't matter - only proximity.

    The acceptance gate in find_balloon_circles already filters out BOM row
    numbers, zone grid labels, and plain dimension values (they have no
    surrounding geometry), so false positives from those sources are handled
    upstream. This function only sees digits that have been confirmed to have
    meaningful nearby geometry.

    BALLOON_PROXIMITY_THRESHOLD_PT: set from real confirmed cases:
    - 1/2 overlapping ovals: center dist = 73.9pt (should flag)
    - 6/7 stacked ovals: center dist = 43.7pt (should flag)
    - 3/4 genuinely overlapping: center dist = 29.8pt (should flag)
    - 15/592 overlapping: center dist = 6.8pt (should flag)
    Conservative upper bound: 80pt covers all real cases with headroom.
    """
    flagged = []
    for i in range(len(balloons)):
        b1 = balloons[i]
        cx1, cy1 = b1["center"]
        for j in range(i + 1, len(balloons)):
            b2 = balloons[j]
            cx2, cy2 = b2["center"]
            dist = ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5
            is_flagged = dist <= BALLOON_PROXIMITY_THRESHOLD_PT
            if debug_log is not None:
                debug_log.append(
                    f"    balloon '{b1['text']}' at ({cx1:.1f},{cy1:.1f}) vs "
                    f"'{b2['text']}' at ({cx2:.1f},{cy2:.1f}): "
                    f"center dist={dist:.1f}pt (threshold={BALLOON_PROXIMITY_THRESHOLD_PT}pt) "
                    f"-> {'FLAGGED' if is_flagged else 'not flagged'}"
                )
            if is_flagged:
                flagged.append((b1, b2))
    return flagged


def find_balloon_overlaps_by_measured_rect(balloons, debug_log=None):
    """Flags pairs of balloons whose measured geometry rects genuinely
    intersect (not merely touch). Uses the inscribed radius = min(w,h)/2
    capped at MEASURED_RECT_MAX_EFFECTIVE_RADIUS_PT so tall/oval balloons
    whose segment gather picked up nearby geometry don't produce a
    wildly inflated r.

    OFF by default (ENABLE_MEASURED_RECT_BALLOON_CHECK = False): was
    causing false positives on stacked/touching balloons before the
    inscribed-radius cap was added. Keep disabled until calibration
    confirms the false-positive rate is acceptable.
    """
    flagged = []
    for i in range(len(balloons)):
        b1 = balloons[i]
        rect1 = b1["rect"]
        r1 = min(min(rect1.width, rect1.height) / 2.0,
                 MEASURED_RECT_MAX_EFFECTIVE_RADIUS_PT)
        cx1, cy1 = b1["center"]
        for j in range(i + 1, len(balloons)):
            b2 = balloons[j]
            rect2 = b2["rect"]
            # Quick rect-intersection check first
            inter = rect1 & rect2
            if inter.is_empty:
                continue
            inter_area = inter.width * inter.height
            if inter_area < MEASURED_RECT_MIN_OVERLAP_AREA_PT2:
                continue
            r2 = min(min(rect2.width, rect2.height) / 2.0,
                     MEASURED_RECT_MAX_EFFECTIVE_RADIUS_PT)
            cx2, cy2 = b2["center"]
            dist = ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5
            # Only flag when centres are closer than exact-tangent minus
            # tolerance - intentional touching groups stay clean.
            threshold = r1 + r2 - MEASURED_RECT_TANGENT_TOLERANCE_PT
            is_flagged = dist < threshold
            if debug_log is not None:
                debug_log.append(
                    f"    [measured-rect] balloon '{b1['text']}' r={r1:.1f}pt vs "
                    f"'{b2['text']}' r={r2:.1f}pt: "
                    f"inter_area={inter_area:.1f}pt² dist={dist:.1f}pt "
                    f"threshold={threshold:.1f}pt "
                    f"-> {'FLAGGED' if is_flagged else 'not flagged'}"
                )
            if is_flagged:
                flagged.append((b1, b2))
    return flagged


def _is_magenta_color(color):
    """True if the RGB triple is close to pure magenta (high R, low G, high B)."""
    if not isinstance(color, (tuple, list)) or len(color) < 3:
        return False
    r, g, b = float(color[0]), float(color[1]), float(color[2])
    return r >= MAGENTA_R_MIN and g <= MAGENTA_G_MAX and b >= MAGENTA_B_MIN


def find_magenta_dimension_clusters(segments, page_rect, debug_log=None):
    """Finds clusters of magenta stroked segments that look like dangling
    Inventor dimensions (high R, low G, high B stroke colour).

    Returns a list of cluster dicts: {"segments": [...], "bbox": fitz.Rect}
    for each cluster that passes all filters.

    Filters applied (in order):
      1. Segment must have a magenta stroke colour.
      2. Segment length >= MAGENTA_MIN_SEGMENT_LENGTH_PT (drops tiny dashes).
      3. Cluster must have >= MAGENTA_MIN_CLUSTER_SEGMENTS members.
      4. Cluster longest axis < MAGENTA_MAX_SPAN_FRACTION_OF_PAGE x page size
         (drops sheet-length centrelines).
    """
    # Collect magenta segments
    mag_segs = []
    for p1, p2, meta in segments:
        if not _is_magenta_color(meta.get("color")):
            continue
        length = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
        if length < MAGENTA_MIN_SEGMENT_LENGTH_PT:
            continue
        mag_segs.append((p1, p2, meta))

    if not mag_segs:
        return []

    # Union-find clustering by proximity
    n = len(mag_segs)
    parent = list(range(n))

    def find_root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find_root(a), find_root(b)
        if ra != rb:
            parent[ra] = rb

    # Build endpoint bboxes for proximity check
    bboxes = []
    for p1, p2, _ in mag_segs:
        x0 = min(p1[0], p2[0]) - MAGENTA_CLUSTER_GAP_PT
        y0 = min(p1[1], p2[1]) - MAGENTA_CLUSTER_GAP_PT
        x1 = max(p1[0], p2[0]) + MAGENTA_CLUSTER_GAP_PT
        y1 = max(p1[1], p2[1]) + MAGENTA_CLUSTER_GAP_PT
        bboxes.append((x0, y0, x1, y1))

    for i in range(n):
        ax0, ay0, ax1, ay1 = bboxes[i]
        for j in range(i + 1, n):
            bx0, by0, bx1, by1 = bboxes[j]
            # Do expanded bboxes overlap?
            if ax1 >= bx0 and bx1 >= ax0 and ay1 >= by0 and by1 >= ay0:
                union(i, j)

    # Group by root
    groups = {}
    for i in range(n):
        root = find_root(i)
        groups.setdefault(root, []).append(i)

    page_w = page_rect.width
    page_h = page_rect.height
    max_span = max(page_w, page_h) * MAGENTA_MAX_SPAN_FRACTION_OF_PAGE

    clusters = []
    for idxs in groups.values():
        if len(idxs) < MAGENTA_MIN_CLUSTER_SEGMENTS:
            continue
        cluster_segs = [mag_segs[i] for i in idxs]
        # Compute bbox of all endpoints
        all_x = [p[0] for p1, p2, _ in cluster_segs for p in (p1, p2)]
        all_y = [p[1] for p1, p2, _ in cluster_segs for p in (p1, p2)]
        bbox = fitz.Rect(min(all_x), min(all_y), max(all_x), max(all_y))
        span = max(bbox.width, bbox.height)
        if span > max_span:
            if debug_log is not None:
                debug_log.append(
                    f"    [magenta] cluster of {len(idxs)} segments skipped: "
                    f"span={span:.0f}pt > max {max_span:.0f}pt (likely centreline)"
                )
            continue
        clusters.append({"segments": cluster_segs, "bbox": bbox})
        if debug_log is not None:
            debug_log.append(
                f"    [magenta] cluster of {len(idxs)} segments: "
                f"bbox=({bbox.x0:.0f},{bbox.y0:.0f})-({bbox.x1:.0f},{bbox.y1:.0f})"
            )

    return clusters


def run_geometry_checks(page, page_num, report_lines, counts, ensure_page_header, words=None):
    """Runs the line-crossing, text-overlap and balloon-overlap checks for
    one page, drawing highlights and updating counts/report in place.

    words: pass the already-fetched page.get_text("words") list from the
    caller to avoid a redundant extraction. If None, fetched here instead."""
    # Use the caller-supplied word list when available (saves one get_text
    # call per page - _process_pdf_impl already extracts words for spelling
    # and passes them in). Keeping the fallback so this function still works
    # standalone if called from outside the main loop.
    if words is None:
        words = page.get_text("words")

    # Fetch ALL page drawings ONCE and share the raw list between the two
    # indexes built below. Previously this called page.get_drawings() twice
    # per page (once for line-crossing, once for balloon detection), which
    # is the dominant PyMuPDF cost on complex pages with hundreds of segments.
    # Both indexes differ only in how extract_segments samples bezier curves
    # (crude_curves=True/False) - the underlying drawings list is identical.
    _raw_drawings = page.get_drawings()

    # Build the segment list + spatial index for line-crossing (accurate
    # curve sampling - see extract_segments). Pass the pre-fetched drawings
    # so get_drawings() isn't called again.
    segments, grid = build_segment_index(page, drawings=_raw_drawings)

    # A well-formed BOM/parts table's own borders should never be flagged
    # as "wrong line crossing text" - that's just how tables are drawn.
    # Confirmed against a real drawing that table row-divider lines
    # (spanning far wider than any single cell - e.g. a 94pt-long gridline
    # crossing a 20pt-wide word) were the dominant remaining false-positive
    # source even after excluding dimension text and dense scribble/
    # watermark clusters. We already reliably locate the BOM table via the
    # same header/column detection the BOM sequence check uses, so exclude
    # that whole region from line-crossing rather than trying to model
    # every possible table-formatting quirk that causes this.
    bom_regions = find_bom_table_regions(page, words)

    # Balloon detection now needs to run BEFORE line-crossing (previously
    # the other way around), so line-crossing can recognize a balloon
    # reference number and exempt it from the "bare digit = probably a
    # dimension value" skip - see the comment inside find_line_crossings
    # for why that skip was silently hiding genuine balloon defects.
    balloon_debug = [] if DEBUG_MODE else None
    balloon_segments, balloon_grid = build_segment_index(page, crude_curves=True, drawings=_raw_drawings)
    balloons = find_balloon_circles(page, balloon_segments, balloon_grid, debug_log=balloon_debug, words=words, bom_regions=bom_regions)
    balloon_flags = (
        find_balloon_overlaps(balloons, debug_log=balloon_debug)
        if (balloons and ENABLE_BALLOON_OVERLAP_CHECK) else []
    )
    known_size_flags = (
        find_balloon_overlaps_known_size(balloons, debug_log=balloon_debug)
        if (balloons and ENABLE_KNOWN_SIZE_BALLOON_CHECK) else []
    )
    balloon_word_keys = {b["word_key"] for b in balloons if b["word_key"] is not None}

    line_flags = find_line_crossings(
        page, segments, grid, exclude_regions=bom_regions,
        balloon_word_keys=balloon_word_keys, report_lines=report_lines, words=words
    )

    # SANITY CIRCUIT-BREAKER: SHX-font AutoCAD text (even with PDFSHX=2's
    # hidden searchable text enabled) still draws every VISIBLE letter as
    # vector line strokes tracing its own shape - meaning ordinary text
    # can appear "crossed by a line" purely because of its own glyph
    # geometry, not an external defect. Confirmed on a real AutoCAD/
    # PDFSHX=2 file: 74 line-crossing + 6 balloon-overlap flags out of
    # ~525 words (~15%) on completely ordinary text (dimension values,
    # caution-notice words) - this is a fundamentally different failure
    # mode from a genuine isolated defect, which should only ever flag a
    # small handful of words on a real drawing. If the combined geometry
    # flags exceed this threshold, treat it as a signature of vector-
    # outlined text rather than 80 real problems, and suppress both
    # checks for this page with a clear explanation instead of drowning
    # the report in false positives.
    total_word_count = max(len(words), 1)
    combined_geometry_flags = len(line_flags) + len(balloon_flags)
    geometry_sanity_threshold = max(
        GEOMETRY_SANITY_MIN_ABSOLUTE,
        round(total_word_count * GEOMETRY_SANITY_MAX_FRACTION),
    )

    if combined_geometry_flags > geometry_sanity_threshold:
        ensure_page_header()
        pct = 100.0 * combined_geometry_flags / total_word_count
        print(f"  Page {page_num + 1}: SUPPRESSED line-crossing/balloon checks - "
              f"{combined_geometry_flags} flags across {total_word_count} words ({pct:.0f}%) "
              f"looks like vector-outlined text, not real defects")
        report_lines.append(
            f"    [GEOMETRY CHECKS SUPPRESSED] {combined_geometry_flags} line-crossing/balloon "
            f"flags across {total_word_count} words ({pct:.0f}%) is far above what a genuine "
            f"defect would produce. This usually means the PDF's text is vector-outlined (e.g. "
            f"AutoCAD SHX fonts, even with PDFSHX=2's hidden text enabled - the VISIBLE letters "
            f"are still drawn as vector strokes tracing their own shape, which line-crossing "
            f"detection can mistake for external defects). Spelling, BOM, REV and other "
            f"position-only checks are unaffected and still ran normally."
        )
        return

    if line_flags:
        counts["line"] += len(line_flags)
        ensure_page_header()
        print(f"  Page {page_num + 1}: {len(line_flags)} word(s) crossed by a line")
        for text, rect, (p1, p2), meta in line_flags:
            report_lines.append(
                f"    [LINE CROSSING] '{text}' is spelled correctly - flagged because a line/leader "
                f"crosses through it (highlighted in ORANGE, not red) at "
                f"({rect.x0:.1f},{rect.y0:.1f})-({rect.x1:.1f},{rect.y1:.1f})  "
                f"segment=({p1[0]:.1f},{p1[1]:.1f})-({p2[0]:.1f},{p2[1]:.1f})  "
                f"source: type={meta.get('type')!r} stroke_color={meta.get('color')} "
                f"fill_color={meta.get('fill')} stroke_opacity={meta.get('stroke_opacity')} "
                f"fill_opacity={meta.get('fill_opacity')} width={meta.get('width')}"
            )
            draw_highlight(page, rect, color=LINE_CROSSING_HIGHLIGHT_COLOR, label="CLASH",
                           label_color=CLASH_LABEL_COLOR, label_fontsize=9.0,
                           label_offset_lines=1.0)

    text_overlap_debug = [] if DEBUG_MODE else None
    overlap_flags = find_text_overlaps(page, debug_log=text_overlap_debug, words=words, exclude_regions=bom_regions)
    if text_overlap_debug:
        report_lines.append(f"    [DEBUG] text-overlap near-misses on page {page_num + 1}:")
        report_lines.extend(text_overlap_debug)
    if overlap_flags:
        counts["text_overlap"] += len(overlap_flags)
        ensure_page_header()
        print(f"  Page {page_num + 1}: {len(overlap_flags)} text-on-text overlap(s)")
        for r1, t1, r2, t2 in overlap_flags:
            report_lines.append(f"    [TEXT OVERLAP] '{t1}' overlaps '{t2}'  near ({r1.x0:.1f},{r1.y0:.1f})")
            union_rect = fitz.Rect(
                min(r1.x0, r2.x0), min(r1.y0, r2.y0),
                max(r1.x1, r2.x1), max(r1.y1, r2.y1),
            )
            draw_highlight(page, union_rect, enlarge=False)

    measured_rect_flags = (
        find_balloon_overlaps_by_measured_rect(balloons, debug_log=balloon_debug)
        if (balloons and ENABLE_MEASURED_RECT_BALLOON_CHECK) else []
    )

    if DEBUG_MODE and balloon_debug:
        ensure_page_header()
        report_lines.append(f"    [DEBUG] balloon candidates on page {page_num + 1}:")
        report_lines.extend(balloon_debug)

    if balloon_flags:
        counts["balloon_overlap"] += len(balloon_flags)
        ensure_page_header()
        print(f"  Page {page_num + 1}: {len(balloon_flags)} balloon-on-balloon overlap(s)")
        for b1, b2 in balloon_flags:
            report_lines.append(
                f"    [BALLOON OVERLAP] balloon '{b1['text']}' overlaps balloon '{b2['text']}'"
                f"  near ({b1['rect'].x0:.1f},{b1['rect'].y0:.1f})"
            )
            union_rect = fitz.Rect(
                min(b1["rect"].x0, b2["rect"].x0), min(b1["rect"].y0, b2["rect"].y0),
                max(b1["rect"].x1, b2["rect"].x1), max(b1["rect"].y1, b2["rect"].y1),
            )
            draw_highlight(page, union_rect, enlarge=False)

    if known_size_flags:
        counts["balloon_overlap"] += len(known_size_flags)
        ensure_page_header()
        print(f"  Page {page_num + 1}: {len(known_size_flags)} known-size BOM balloon overlap(s)")
        for b1, b2 in known_size_flags:
            cx1, cy1 = b1["center"]
            cx2, cy2 = b2["center"]
            report_lines.append(
                f"    [BALLOON OVERLAP - KNOWN SIZE] BOM balloon '{b1['text']}' overlaps "
                f"balloon '{b2['text']}'  near ({cx1:.1f},{cy1:.1f})"
            )
            # Highlight rect built from the KNOWN radius around each real
            # centre, not from any measured/estimated shape - this is the
            # one piece of geometry this check actually has confidence in.
            r = BOM_BALLOON_RADIUS_PT
            union_rect = fitz.Rect(
                min(cx1, cx2) - r, min(cy1, cy2) - r,
                max(cx1, cx2) + r, max(cy1, cy2) + r,
            )
            draw_highlight(page, union_rect, enlarge=False)

    if measured_rect_flags:
        counts["balloon_overlap"] += len(measured_rect_flags)
        ensure_page_header()
        print(f"  Page {page_num + 1}: {len(measured_rect_flags)} measured-rect balloon overlap(s)")
        for b1, b2 in measured_rect_flags:
            cx1, cy1 = b1["center"]
            cx2, cy2 = b2["center"]
            report_lines.append(
                f"    [BALLOON OVERLAP - MEASURED RECT] balloon '{b1['text']}' overlaps "
                f"balloon '{b2['text']}'  near ({cx1:.1f},{cy1:.1f})"
            )
            union_rect = fitz.Rect(
                min(b1["rect"].x0, b2["rect"].x0), min(b1["rect"].y0, b2["rect"].y0),
                max(b1["rect"].x1, b2["rect"].x1), max(b1["rect"].y1, b2["rect"].y1),
            )
            draw_highlight(page, union_rect, enlarge=False, label="BALLOON")

    # A balloon's own outline overlapping unrelated drawing detail - a
    # DIFFERENT problem from balloon-vs-balloon overlap above. Uses the
    # two-path foreign-segment detection inside find_balloon_circles:
    # colour path (segment colour != balloon dominant colour) AND spatial
    # path (segment endpoint outside outline, midpoint inside core) for
    # monotone drawings. Controlled by its OWN flag so it still works
    # when ENABLE_BALLOON_OVERLAP_CHECK is off.
    geometry_overlap_balloons = (
        [b for b in balloons if b.get("overlaps_geometry")]
        if ENABLE_BALLOON_GEOMETRY_OVERLAP_CHECK else []
    )
    if geometry_overlap_balloons:
        counts["balloon_overlap"] += len(geometry_overlap_balloons)
        ensure_page_header()
        print(f"  Page {page_num + 1}: {len(geometry_overlap_balloons)} balloon(s) overlapping drawing detail")
        for b in geometry_overlap_balloons:
            report_lines.append(
                f"    [BALLOON/GEOMETRY OVERLAP] balloon '{b['text']}' outline overlaps "
                f"drawing detail ({b['foreign_segment_count']} non-balloon-color segment(s) "
                f"within its own outline)  at ({b['rect'].x0:.1f},{b['rect'].y0:.1f})-"
                f"({b['rect'].x1:.1f},{b['rect'].y1:.1f})"
            )
            draw_highlight(page, b["rect"], enlarge=False, label="CLASH",
                           label_color=CLASH_LABEL_COLOR, label_fontsize=9.0,
                           label_offset_lines=1.0)

    # Geometry-only circle crossing check - detects any two circular shapes
    # whose boundaries physically cross, regardless of whether they contain
    # text or are recognised as balloons. Needed for empty section/detail
    # marker circles and any other annotation circles.
    circle_debug = [] if (DEBUG_MODE and ENABLE_CIRCLE_CROSSING_CHECK) else None
    circle_flags = (
        find_crossing_circles(page, segments, grid, debug_log=circle_debug)
        if ENABLE_CIRCLE_CROSSING_CHECK else []
    )
    if circle_debug:
        report_lines.append(f"    [DEBUG] circle crossing check on page {page_num + 1}:")
        report_lines.extend(circle_debug)
    if circle_flags:
        counts["balloon_overlap"] += len(circle_flags)
        ensure_page_header()
        print(f"  Page {page_num + 1}: {len(circle_flags)} crossing circle pair(s)")
        for cx1,cy1,r1,cx2,cy2,r2,union_rect in circle_flags:
            report_lines.append(
                f"    [CIRCLE CROSSING] two circular shapes cross each other: "
                f"circle at ({cx1:.0f},{cy1:.0f}) r={r1:.0f}pt "
                f"vs ({cx2:.0f},{cy2:.0f}) r={r2:.0f}pt"
            )
            draw_highlight(page, union_rect, enlarge=False)

    # Shape clash check - assembles whole shapes by tracing shared
    # endpoints between segments, then tests exact segment intersection.
    # Replaces the balloon-overlap and circle-crossing checks above, both
    # of which relied on estimating a centre and radius from clustered
    # segments; wrong estimates were the direct cause of their 152 and
    # 246 false flags on a 30-drawing batch.
    if ENABLE_SHAPE_CLASH_CHECK:
        shape_debug = [] if DEBUG_MODE else None
        traced_shapes = trace_connected_shapes(page, debug_log=shape_debug)
        shape_flags = find_shape_clashes(traced_shapes, debug_log=shape_debug)
        if shape_debug:
            report_lines.append(f"    [DEBUG] shape clash check on page {page_num + 1}:")
            report_lines.extend(shape_debug)
        if shape_flags:
            counts["balloon_overlap"] += len(shape_flags)
            ensure_page_header()
            print(f"  Page {page_num + 1}: {len(shape_flags)} shape clash(es)")
            for s1, s2, union_rect in shape_flags:
                r1s, r2s = s1["rect"], s2["rect"]
                report_lines.append(
                    f"    [SHAPE CLASH] two drawn shapes cross each other: "
                    f"shape at ({r1s.x0:.0f},{r1s.y0:.0f}) "
                    f"{r1s.x1-r1s.x0:.0f}x{r1s.y1-r1s.y0:.0f}pt "
                    f"crosses shape at ({r2s.x0:.0f},{r2s.y0:.0f}) "
                    f"{r2s.x1-r2s.x0:.0f}x{r2s.y1-r2s.y0:.0f}pt"
                )
                draw_highlight(page, union_rect, enlarge=False)

    # Magenta / dangling-dimension check: clusters of magenta stroked
    # segments that look like Inventor "sick" dimensions (lost geometric
    # association). Centrelines filtered out by span size.
    if ENABLE_MAGENTA_DIMENSION_CHECK:
        magenta_debug = [] if DEBUG_MODE else None
        magenta_clusters = find_magenta_dimension_clusters(
            segments, page.rect, debug_log=magenta_debug
        )
        if magenta_debug:
            report_lines.append(f"    [DEBUG] magenta dimension check on page {page_num + 1}:")
            report_lines.extend(magenta_debug)
        if magenta_clusters:
            counts["magenta_dimension"] += len(magenta_clusters)
            ensure_page_header()
            print(f"  Page {page_num + 1}: {len(magenta_clusters)} magenta/dangling dimension(s)")
            for cluster in magenta_clusters:
                bbox = cluster["bbox"]
                report_lines.append(
                    f"    [MAGENTA DIMENSION] {len(cluster['segments'])} magenta segment(s) "
                    f"clustered at ({bbox.x0:.0f},{bbox.y0:.0f})-({bbox.x1:.0f},{bbox.y1:.0f}) "
                    f"- possible dangling/sick Inventor dimension"
                )
                draw_highlight(page, bbox, enlarge=True,
                               color=MAGENTA_HIGHLIGHT_COLOR, label="DANGLING")

    return balloons


# ==================================================================
# CHECK 2: BOM item-number sequence
# ==================================================================

# --- Geometry circle crossing detection ---
# Min diagonal segment length to count toward a circle cluster - very short
# diagonals are just SHX glyph strokes or arrow tips, not circle arcs
CIRCLE_MIN_SEGMENT_LENGTH_PT = 1.0
# Max segment length for circle arc segments - long diagonals are leader
# lines or hatching, not circle arcs
CIRCLE_MAX_SEGMENT_LENGTH_PT = 25.0
# Minimum segments in a cluster to be considered a real circle
CIRCLE_MIN_CLUSTER_SEGMENTS = 6
# Search radius for clustering diagonal segments into circles
CIRCLE_CLUSTER_RADIUS_PT = 35.0
# Two circles whose centres are closer than r1+r2+this margin are flagged
# as crossing. A small positive margin catches circles that are genuinely
# crossing but where our radius estimate is slightly short. Confirmed from
# real geometry: touching circles have centre distance ≈ r1+r2 exactly,
# crossing ones have distance < r1+r2. A margin of 0 flags crossings only;
# increase to also catch very-close-but-not-quite-touching pairs.
CIRCLE_OVERLAP_MARGIN_PT = 5.0
# Minimum and maximum radius for a shape to be considered a circle worth
# checking - filters out tiny arrowheads and giant page borders
CIRCLE_MIN_RADIUS_PT = 10.0
CIRCLE_MAX_RADIUS_PT = 200.0


# --- Connected-shape clash detection ---
# Endpoint match tolerance when joining segments into shapes. Real data
# shows the same corner reported as 1061.30 and 1061.31 by different
# drawing objects, so an exact match fails - but the gap is tiny.
SHAPE_ENDPOINT_TOLERANCE_PT = 0.5
# A shape must be at least this big in both axes to be worth checking -
# filters out tiny fragments, arrow tips and glyph strokes.
SHAPE_MIN_SIZE_PT = 8.0
# ...and no bigger than this, to exclude page borders and frame lines.
SHAPE_MAX_SIZE_PT = 300.0
# Ignore shapes made of more segments than this - dense hatching and
# vector-outlined text, not annotation shapes.
SHAPE_MAX_SEGMENTS = 200


def trace_connected_shapes(page, debug_log=None):
    """Assembles drawing segments into whole SHAPES by following shared
    endpoints, across separate PDF drawing objects.

    This exists because neither simpler approach works on real files:
      - PDF closed-path flags are useless here: confirmed on a real
        drawing that every relevant drawing object reports
        closePath=False, including a perfectly closed balloon outline.
      - One-drawing-object-per-shape is false: that same balloon outline
        was split across FIVE drawing objects (#111,#112,#113,#114,#116).

    What IS reliable is that the pieces meet end-to-end. Tracing shared
    endpoints reassembled that balloon exactly (w=70.88 h=42.53) and its
    neighbour independently (w=70.86 h=42.53) - identical dimensions with
    no radius estimation or proximity clustering anywhere, which is what
    made every previous version of this check unreliable. The balloon's
    inner text divider correctly fell out as its own separate shape.

    Returns a list of dicts: {"segments": [(p1,p2),...], "rect": fitz.Rect}
    """
    # Snap endpoints to a grid so near-identical coordinates collide,
    # giving O(n) lookup instead of an O(n^2) all-pairs comparison.
    def key_of(pt):
        return (round(pt[0] / SHAPE_ENDPOINT_TOLERANCE_PT),
                round(pt[1] / SHAPE_ENDPOINT_TOLERANCE_PT))

    raw = []
    for d in page.get_drawings():
        if not drawing_is_visible(d):
            continue
        for item in d.get("items", []):
            kind = item[0]
            if kind == "l":
                raw.append(((item[1].x, item[1].y), (item[2].x, item[2].y)))
            elif kind == "c":
                # Endpoints only - p0 and p3 are the real on-curve points
                raw.append(((item[1].x, item[1].y), (item[4].x, item[4].y)))
            elif kind == "re":
                r = item[1]
                c = [(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)]
                for i in range(4):
                    raw.append((c[i], c[(i + 1) % 4]))

    if not raw:
        return []

    parent = list(range(len(raw)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    # Bucket segments by each endpoint; anything sharing a bucket joins.
    buckets = {}
    for idx, (p1, p2) in enumerate(raw):
        for pt in (p1, p2):
            buckets.setdefault(key_of(pt), []).append(idx)
    for members in buckets.values():
        first = members[0]
        for other in members[1:]:
            union(first, other)

    grouped = {}
    for idx in range(len(raw)):
        grouped.setdefault(find(idx), []).append(idx)

    shapes = []
    for members in grouped.values():
        if len(members) > SHAPE_MAX_SEGMENTS:
            continue
        segs = [raw[m] for m in members]
        xs = [p[0] for s in segs for p in s]
        ys = [p[1] for s in segs for p in s]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if not (SHAPE_MIN_SIZE_PT <= w <= SHAPE_MAX_SIZE_PT):
            continue
        if not (SHAPE_MIN_SIZE_PT <= h <= SHAPE_MAX_SIZE_PT):
            continue
        shapes.append({
            "segments": segs,
            "rect": fitz.Rect(min(xs), min(ys), max(xs), max(ys)),
        })

    if debug_log is not None:
        debug_log.append(
            f"    traced {len(shapes)} candidate shape(s) from {len(raw)} segments"
        )
    return shapes


def find_shape_clashes(shapes, debug_log=None):
    """Flags pairs of traced shapes whose outlines actually cross.

    Uses exact segment-vs-segment intersection, not bounding-box overlap:
    two shapes can have overlapping bboxes without touching (an L-bracket
    beside a circle), and only a real segment crossing is a real clash.
    Nothing here estimates a centre or a radius, which is what made the
    previous balloon/circle checks produce 152 and 246 false flags on a
    30-drawing batch.
    """
    flagged = []
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            r1, r2 = shapes[i]["rect"], shapes[j]["rect"]
            if (r1 & r2).is_empty:
                continue  # cheap reject before the exact test
            hit = None
            for a1, a2 in shapes[i]["segments"]:
                for b1, b2 in shapes[j]["segments"]:
                    if segments_intersect(a1, a2, b1, b2):
                        hit = (a1, a2, b1, b2)
                        break
                if hit:
                    break
            if hit:
                union_rect = fitz.Rect(
                    min(r1.x0, r2.x0), min(r1.y0, r2.y0),
                    max(r1.x1, r2.x1), max(r1.y1, r2.y1),
                )
                flagged.append((shapes[i], shapes[j], union_rect))
                if debug_log is not None:
                    debug_log.append(
                        f"    [SHAPE CLASH] shape at ({r1.x0:.0f},{r1.y0:.0f}) "
                        f"{r1.x1-r1.x0:.0f}x{r1.y1-r1.y0:.0f} crosses shape at "
                        f"({r2.x0:.0f},{r2.y0:.0f}) {r2.x1-r2.x0:.0f}x{r2.y1-r2.y0:.0f}"
                    )
    return flagged


def find_crossing_circles(page, segments, grid, debug_log=None):
    """Detects pairs of circular/oval drawing shapes whose boundaries
    physically cross each other — regardless of whether they contain text,
    are labelled as balloons, or are any specific shape type. Confirmed
    necessary on a real drawing: section-marker circles (drawn as many short
    diagonal line segments approximating a circle) were crossing each other
    with no text inside them, so the existing text-anchored balloon detection
    couldn't find them at all.

    Approach: cluster all short diagonal segments on the page (non-axis-
    aligned, short enough to be a circle arc rather than a leader or border
    line) into circular shapes by proximity, estimate each circle's centre
    and radius from its segments, then flag pairs where centre distance <
    r1 + r2 + CIRCLE_OVERLAP_MARGIN_PT.

    Returns list of (centre1, radius1, centre2, radius2, rect) tuples.
    """
    drawings = page.get_drawings()
    # Collect all diagonal short segments grouped by drawing object.
    # Each drawing object in the PDF is a separate shape - so segments
    # from the same drawing index belong to the same circle/arc.
    # Group by drawing index first, then cluster groups by proximity.
    drawing_groups = {}  # drawing_idx -> list of (x1,y1,x2,y2)
    for d_idx, d in enumerate(drawings):
        if not drawing_is_visible(d):
            continue
        for item in d.get("items", []):
            if item[0] != "l":
                continue
            p1, p2 = item[1], item[2]
            dx, dy = abs(p2.x - p1.x), abs(p2.y - p1.y)
            length = (dx**2 + dy**2) ** 0.5
            if (dx > 0.5 and dy > 0.5 and
                    CIRCLE_MIN_SEGMENT_LENGTH_PT <= length <= CIRCLE_MAX_SEGMENT_LENGTH_PT):
                drawing_groups.setdefault(d_idx, []).append((p1.x, p1.y, p2.x, p2.y))

    # Each drawing group with enough diagonal segments is a candidate circle.
    # If a group has too few segments on its own, merge it with the nearest
    # group that it's close to (handles circles split across multiple drawing objects).
    candidate_groups = []
    for d_idx, segs in drawing_groups.items():
        if len(segs) >= CIRCLE_MIN_CLUSTER_SEGMENTS:
            mids = [((s[0]+s[2])/2, (s[1]+s[3])/2) for s in segs]
            ccx = sum(m[0] for m in mids)/len(mids)
            ccy = sum(m[1] for m in mids)/len(mids)
            candidate_groups.append((ccx, ccy, segs, d_idx))

    if not candidate_groups:
        # Fall back to proximity clustering if drawing-object approach found nothing
        diag_segments = []
        for d_idx, segs in drawing_groups.items():
            diag_segments.extend(segs)
        used = set()
        for i, (x1,y1,x2,y2) in enumerate(diag_segments):
            if i in used: continue
            cx, cy = (x1+x2)/2, (y1+y2)/2
            cluster_idx = [i]
            for j, (ox1,oy1,ox2,oy2) in enumerate(diag_segments):
                if j == i or j in used: continue
                mx, my = (ox1+ox2)/2, (oy1+oy2)/2
                if (mx-cx)**2 + (my-cy)**2 < CIRCLE_CLUSTER_RADIUS_PT**2:
                    cluster_idx.append(j)
            if len(cluster_idx) >= CIRCLE_MIN_CLUSTER_SEGMENTS:
                used.update(cluster_idx)
                mids = [((diag_segments[k][0]+diag_segments[k][2])/2,
                         (diag_segments[k][1]+diag_segments[k][3])/2) for k in cluster_idx]
                ccx = sum(m[0] for m in mids)/len(mids)
                ccy = sum(m[1] for m in mids)/len(mids)
                candidate_groups.append((ccx, ccy,
                    [(diag_segments[k][0],diag_segments[k][1],diag_segments[k][2],diag_segments[k][3])
                     for k in cluster_idx], -1))

    if len(candidate_groups) < 2:
        return []

    # Check all pairs
    circles = []
    for ccx, ccy, segs, d_idx in candidate_groups:
        all_pts = [(s[0],s[1]) for s in segs] + [(s[2],s[3]) for s in segs]
        radii_sorted = sorted(((px-ccx)**2+(py-ccy)**2)**0.5 for px,py in all_pts)
        radius = radii_sorted[len(radii_sorted)//2]  # median
        if CIRCLE_MIN_RADIUS_PT <= radius <= CIRCLE_MAX_RADIUS_PT:
            circles.append((ccx, ccy, radius))
            if debug_log is not None:
                debug_log.append(
                    f"    circle at ({ccx:.1f},{ccy:.1f}) r={radius:.1f}pt "
                    f"from {len(segs)} segments (drawing #{d_idx})"
                )

    flagged = []
    for i in range(len(circles)):
        cx1,cy1,r1 = circles[i]
        for j in range(i+1, len(circles)):
            cx2,cy2,r2 = circles[j]
            dist = ((cx2-cx1)**2+(cy2-cy1)**2)**0.5
            if dist < r1 + r2 + CIRCLE_OVERLAP_MARGIN_PT:
                # Circles cross - build a highlight rect spanning the overlap area
                union_rect = fitz.Rect(
                    min(cx1-r1, cx2-r2), min(cy1-r1, cy2-r2),
                    max(cx1+r1, cx2+r2), max(cy1+r1, cy2+r2),
                )
                flagged.append((cx1,cy1,r1, cx2,cy2,r2, union_rect))
                if debug_log is not None:
                    debug_log.append(
                        f"    [CIRCLE CROSSING] circle at ({cx1:.0f},{cy1:.0f}) r={r1:.0f} "
                        f"vs ({cx2:.0f},{cy2:.0f}) r={r2:.0f}: dist={dist:.1f} < r1+r2={r1+r2:.1f}"
                    )
    return flagged


def find_bom_headers(words):
    """A genuine BOM table header row always has ITEM, QTY, AND
    DESCRIPTION together - requiring all three (not just ITEM+QTY) avoids
    matching incidental "ITEM ... QTY-ish" text elsewhere on the page.
    Confirmed on a real drawing: a NOTES paragraph mentioning "ITEM 2" and
    similar item-number references got matched as a BOM header using the
    ITEM+QTY-only check, producing a completely spurious "table" built
    from unrelated note numbers."""
    item_words = [w for w in words if w[4].strip() == "ITEM"]
    qty_words  = [w for w in words if w[4].strip() == "QTY"]
    desc_words = [w for w in words if w[4].strip() == "DESCRIPTION"]
    headers = []
    for iw in item_words:
        iy = (iw[1] + iw[3]) / 2
        qty_match = None
        for qw in qty_words:
            qy = (qw[1] + qw[3]) / 2
            if abs(iy - qy) <= HEADER_ROW_TOLERANCE_PT:
                qty_match = qw
                break
        if qty_match is None:
            continue
        desc_match = any(
            abs(iy - (dw[1] + dw[3]) / 2) <= HEADER_ROW_TOLERANCE_PT
            for dw in desc_words
        )
        if desc_match:
            headers.append(iw)
    return headers


# How far left of QTY, and how wide, to estimate the ITEM column sits
# when using the OCR-only fallback below - typical single/double-digit
# item-number column proportions observed on real BOM tables.
#
# Widened after a real test: an earlier, narrower estimate (5pt gap,
# 35pt wide) found NOTHING - fewer than 3 digit-shaped words in that
# band, meaning it missed the real column entirely. A too-wide net here
# only risks picking up a few stray unrelated digits (still filtered by
# extract_item_column's own row-clustering logic); a too-narrow net
# finds nothing at all, which is the worse failure - so this errs
# generous rather than trying to pinpoint an exact width from a single
# data point.
RELAXED_ITEM_COL_GAP_PT = 2.0
RELAXED_ITEM_COL_WIDTH_PT = 90.0


def find_bom_headers_relaxed(words):
    """Fallback used only when the strict ITEM+QTY+DESCRIPTION match above
    finds nothing, and only on OCR-sourced pages (see run_bom_sequence_check)
    - the same real BOM header row confirmed via two independently strong
    signals (QTY and DESCRIPTION aligned) without also requiring 'ITEM'
    text to be found.

    Confirmed necessary on a real rotated file: every other header-row
    word (QTY, DESCRIPTION, PART No./SPECIFICATION, MASS (KG)) was read
    correctly by OCR - confirmed by dumping the ENTIRE row, full page
    width - but 'ITEM' itself was genuinely absent from OCR's output on
    that row, not misread as something else, even after every other
    targeted fix in this rotation-handling effort (higher DPI, lower
    confidence floor, self-correcting rotation direction). QTY+DESCRIPTION
    aligned is already a solid two-signal match on its own - this isn't
    lowering the bar to a single ambiguous word the way ITEM-alone would.

    Returns a list of "virtual header" word-tuples with an ESTIMATED
    (not OCR-read) position for where the ITEM column sits, immediately
    left of QTY - suitable for extract_item_column() exactly like a real
    header word would be, since that function only uses the header's own
    x-range to define the column boundary."""
    qty_words = [w for w in words if w[4].strip() == "QTY"]
    desc_words = [w for w in words if w[4].strip() == "DESCRIPTION"]
    headers = []
    for qw in qty_words:
        qy = (qw[1] + qw[3]) / 2
        desc_match = any(
            abs(qy - (dw[1] + dw[3]) / 2) <= HEADER_ROW_TOLERANCE_PT for dw in desc_words
        )
        if not desc_match:
            continue
        item_col_x1 = qw[0] - RELAXED_ITEM_COL_GAP_PT
        item_col_x0 = item_col_x1 - RELAXED_ITEM_COL_WIDTH_PT
        headers.append((item_col_x0, qw[1], item_col_x1, qw[3], "ITEM(estimated)", qw[5], qw[6], qw[7]))
    return headers


def extract_item_column(words, header):
    hx0, hx1 = header[0], header[2]
    col_x0, col_x1 = hx0 - COLUMN_MARGIN_PT, hx1 + COLUMN_MARGIN_PT
    col_words = []
    seen_positions = set()
    for w in words:
        x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4].strip()
        if not re.fullmatch(r"\d{1,3}", text):
            continue
        cx = (x0 + x1) / 2
        if not (col_x0 <= cx <= col_x1):
            continue
        # Some title blocks simulate bold by drawing the exact same glyph
        # twice at the exact same position rather than using a real bold
        # font - guards against that duplicate-glyph case specifically.
        pos_key = (text, round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1))
        if pos_key in seen_positions:
            continue
        seen_positions.add(pos_key)
        col_words.append(w)
    col_words.sort(key=lambda w: w[1])

    # The x-range check above only constrains horizontal position - it has
    # no idea where the table's rows actually are vertically, so ANY
    # digit-shaped word anywhere on the page that happens to land in that
    # narrow x-band gets swept in too. Confirmed on a real drawing: an
    # unrelated item-reference balloon ("8", part of a "7 8 8 6" callout
    # cluster elsewhere in the drawing body) coincidentally sat in the
    # same x-band as the BOM table's ITEM column, ~1050pt above the real
    # table - it sorted to the front of the row list and broke the
    # descending sequence, even though the real table (8,7,6,5,4,3,2,1)
    # was completely correct on its own.
    #
    # Real BOM rows are evenly spaced (a few points apart, one text line
    # per row) with nothing else in that x-band between them - so real
    # rows always form one tight, contiguous vertical run. Keep only the
    # largest such run and drop anything separated from it by a much
    # bigger gap; a stray balloon or dimension elsewhere on the page will
    # be hundreds of points away, nowhere close to a genuine row-to-row
    # gap.
    if len(col_words) > 2:
        gaps = [col_words[i + 1][1] - col_words[i][1] for i in range(len(col_words) - 1)]
        median_gap = sorted(gaps)[len(gaps) // 2]
        max_gap = max(ROW_CLUSTER_MIN_GAP_PT, median_gap * ROW_CLUSTER_GAP_MULTIPLIER)
        runs = [[col_words[0]]]
        for w, gap in zip(col_words[1:], gaps):
            if gap <= max_gap:
                runs[-1].append(w)
            else:
                runs.append([w])
        col_words = max(runs, key=len)

    return col_words


# A word whose reported bounding box extends beyond the page's own
# dimensions cannot correspond to anything a person would actually see and
# verify - regardless of the exact underlying cause. Confirmed on a real
# drawing that this happens (a corner 'REV' match at y=951.9 on an 842pt-
# tall page, contributing to a wrong REV value and misleading downstream
# results); pdfplumber's own extraction disagreed on the real position for
# some of this content, and the most likely explanation is that it's tied
# to how bounding boxes get computed for rotated text (this template's
# vertical file-path watermark and margin labels) - but the exact
# mechanism doesn't matter for the fix: never trust a coordinate outside
# the physical page, whatever produced it.
PAGE_BOUNDS_TOLERANCE_PT = 5.0


class OnPageWordsProxy:
    """Wraps a real fitz page, filtering get_text("words") to exclude any
    word positioned outside the page's own visible bounds. Every other
    method/attribute (insert_text, new_shape, search_for, rect,
    get_drawings) passes straight through to the real page unchanged, so
    every existing check function is protected with zero modification.

    NOTE: an earlier version of this class also applied
    page.derotation_matrix to correct word coordinates for pages with a
    rotation flag (confirmed via diagnostic dump that get_text("words")
    returns raw, pre-rotation coordinates on such pages, which was the
    root cause of several REV-detection and false-positive bugs on one
    template family). That approach was REVERTED after it broke highlight
    placement: the corrected coordinates get reused when DRAWING each
    highlight too, and PyMuPDF's drawing operations (new_shape/draw_rect,
    insert_text) expect the page's ORIGINAL native coordinate frame, not
    the corrected one - so highlights started landing in the wrong visual
    position, which is a worse problem than the one being fixed. A
    correct fix needs to keep detection-only coordinates separate from
    the coordinates actually used for drawing, rather than replacing the
    word tuples wholesale - not yet re-implemented."""

    def __init__(self, real_page):
        self._real_page = real_page
        self._cache = None

    def get_text(self, kind="text"):
        if kind != "words":
            return self._real_page.get_text(kind)
        if self._cache is None:
            raw = self._real_page.get_text("words")
            w = self._real_page.rect.width
            h = self._real_page.rect.height
            self._cache = [
                word for word in raw
                if word[0] >= -PAGE_BOUNDS_TOLERANCE_PT
                and word[1] >= -PAGE_BOUNDS_TOLERANCE_PT
                and word[2] <= w + PAGE_BOUNDS_TOLERANCE_PT
                and word[3] <= h + PAGE_BOUNDS_TOLERANCE_PT
            ]
        return self._cache

    def __getattr__(self, name):
        return getattr(self._real_page, name)


# Extra vertical padding (points) above/below the detected item-number rows
# when building a BOM table's exclusion region, since a DESCRIPTION or
# PART No. cell can wrap onto a second line taller than the single-line
# item-number row that anchors the detection
class RotationAwarePageProxy:
    """NOT CURRENTLY USED - process_pdf() no longer constructs this.
    Two attempts at getting the direction of PyMuPDF's rotation_matrix /
    derotation_matrix right for this each produced a different, confirmed
    -wrong result on a real file (row-index letters landing in two
    different wrong places), with no way to run PyMuPDF here to verify
    which direction is actually correct. Replaced by an OCR-based
    approach for the same problem (render + Tesseract, reusing the
    already-proven zero-text-page pipeline) which sidesteps needing this
    matrix math at all - see the per-page rotation handling in
    _process_pdf_impl. Left here in case the matrix-direction question
    ever gets a definitive answer worth returning to.

    Wraps a real fitz page that has a non-zero /Rotate, presenting a
    landscape-normalized view to structural checks: get_text("words")
    comes back transformed into a standard, unrotated landscape frame,
    and drawing (new_shape/draw_rect, used by draw_highlight) transforms
    a rect from that normalized frame back to the page's real current
    coordinate space before actually drawing - so a check function can
    work entirely in normal landscape coordinates with zero awareness
    that the underlying page is rotated, while a resulting highlight
    still lands in the correct spot on the real, unmodified page.

    Direction note (got this backwards once already, worth being
    explicit): get_text()/get_drawings() return coordinates in the
    page's CURRENT display space already - confirmed via a real page
    where every returned word coordinate fell inside the CURRENT
    (rotated, portrait) page.rect, matching exactly how the file
    actually renders in a real PDF viewer. They are NOT "pre-rotation
    raw" coordinates needing a forward rotation applied - they need the
    INVERSE (derotation_matrix) applied to reach a landscape-normalized
    frame, and the forward rotation_matrix to go back the other way when
    drawing. An earlier version had this exactly backwards, which
    produced a real, confirmed bug: a drawing's row-index letters ("H G
    F...") were normalizing to a horizontal line along the top instead
    of the vertical line down the margin where they actually belong.

    This is the fix OnPageWordsProxy's docstring flagged as needed but
    not yet done: detection coordinates and drawing coordinates were
    getting conflated before (correcting one broke the other). Keeping
    them properly separate - correct normalized coordinates for reading,
    with an explicit inverse transform applied only at the moment of
    drawing - is what makes both work at once.

    Only meant for the specific checks that assume a standard landscape
    layout (BOM table, REV corner, title-block) - spelling, line-crossing,
    text-overlap, and balloon-overlap don't care about page orientation at
    all and should keep using the real page directly, unwrapped.
    """

    def __init__(self, real_page):
        self._real_page = real_page
        self._to_normalized = real_page.derotation_matrix  # current display -> landscape-normalized
        self._to_display = real_page.rotation_matrix        # landscape-normalized -> current display
        self._cache = None

    def get_text(self, kind="text"):
        if kind != "words":
            return self._real_page.get_text(kind)
        if self._cache is None:
            raw = self._real_page.get_text("words")
            transformed = []
            for w in raw:
                r = fitz.Rect(w[0], w[1], w[2], w[3]) * self._to_normalized
                x0, x1 = sorted((r.x0, r.x1))
                y0, y1 = sorted((r.y0, r.y1))
                transformed.append((x0, y0, x1, y1) + tuple(w[4:]))
            self._cache = transformed
        return self._cache

    def new_shape(self):
        return _RotationAwareShape(self._real_page.new_shape(), self._to_display)

    def __getattr__(self, name):
        return getattr(self._real_page, name)


class _RotationAwareShape:
    """Pairs with RotationAwarePageProxy.new_shape(): draw_rect() converts
    a landscape-normalized rect back to the real page's current display
    coordinates before delegating to the real shape. Every other method
    (finish, commit) passes straight through unchanged."""

    def __init__(self, real_shape, to_display_matrix):
        self._real_shape = real_shape
        self._to_display = to_display_matrix

    def draw_rect(self, rect):
        r = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1) * self._to_display
        x0, x1 = sorted((r.x0, r.x1))
        y0, y1 = sorted((r.y0, r.y1))
        return self._real_shape.draw_rect(fitz.Rect(x0, y0, x1, y1))

    def __getattr__(self, name):
        return getattr(self._real_shape, name)


# A handful of words that reliably appear somewhere in this company's
# title block on virtually every drawing - used to automatically pick
# the correct rotation direction in find_best_rotation_setting (the
# text-extraction-based /Rotate metadata fix) instead of trusting a
# guessed sign convention, which has been wrong three separate times now
# across three different approaches.
_ORIENTATION_PROBE_KEYWORDS = {
    "ITEM", "SCALE", "REV", "APPROVED", "DRAWN", "CHECKED",
    "DESCRIPTION", "QTY", "DATE", "REVISIONS",
}


def _keyword_hits(words):
    return sum(1 for w in words if w[4].strip().upper() in _ORIENTATION_PROBE_KEYWORDS)


# Minimum keyword score before a rotation correction is trusted at all.
# Confirmed necessary on a real drawing: all four rotation candidates
# scored 0 title-block keyword matches (no real evidence for ANY
# orientation), yet the code still picked one and rotated an already-
# correctly-displaying PDF the wrong way. A non-zero /Rotate flag is
# valid, normal PDF structure by itself (many exporters, AutoCAD
# included, use it as part of correctly displaying a page) - it is not
# in itself evidence that anything is wrong. Below this minimum, there
# is no real signal either way, so the safer default is to leave the
# file's rotation untouched rather than guess.
MIN_ROTATION_CONFIDENCE_SCORE = 3


def find_best_rotation_setting(src_path, debug_log=None):
    """NOT CURRENTLY USED - confirmed broken and removed from the main
    pipeline (see process_pdf). Kept only as a documented dead end,
    consistent with the other abandoned rotation approaches in this file.

    CONFIRMED BROKEN: this tries each of the 4 possible /Rotate values
    (0/90/180/270) and scores get_text("words") results by keyword count,
    on the assumption that page.set_rotation(candidate) changes what
    get_text() returns. Direct diagnostic evidence on two real files
    proved this false: page.set_rotation(candidate) followed immediately
    by page.get_text("words") returned the IDENTICAL word list and
    coordinates for every one of the four candidates. get_text() reads
    the underlying content stream, which /Rotate (a pure display-time
    transform) does not affect - so this function could never actually
    distinguish a correct rotation from an incorrect one. Confirmed on a
    real batch: two files that were already displaying correctly both
    got "corrected" to 0deg (the first candidate tried, since a tie never
    beats the current best) and came out visibly wrong.

    Originally: Tries each of the 4 possible /Rotate values (0/90/180/270) on the
    first page and extracts REAL text for each - no OCR needed here,
    since page.set_rotation() is a pure metadata change (confirmed by a
    real, working standalone script that does exactly this: pdf_rotator.py)
    and get_text("words") reads correctly once that flag matches how the
    content should actually display. Picks whichever value produces the
    most real title-block keyword matches (see _ORIENTATION_PROBE_KEYWORDS)
    - the same self-correcting principle already proven for the OCR
    pipeline, but cheaper and more accurate here since it's real
    extracted text, not a lossy OCR read.

    UNVERIFIED ASSUMPTION, flagged directly rather than silently trusted:
    this only works if get_text("words") actually returns DIFFERENT
    results (different words found, and/or different coordinates) across
    the four candidates. If /Rotate is purely a display-time transform
    that doesn't affect which text-showing operators get read from the
    content stream, every candidate could score identically, and 0 would
    always win by being tried first (score > best_score never lets a tie
    overturn it) - regardless of the page's actual correct rotation.
    Confirmed on a real batch: two files with genuine 5-keyword-match
    scores were both "auto-picked" to 0deg and came out visibly wrong.
    That's consistent with this exact failure mode. Debug logging added
    below to directly confirm or rule it out - see debug_log parameter.

    Returns (winning_rotation, keyword_score).
    """
    best_rotation, best_score = 0, -1
    per_candidate = []
    for candidate in (0, 90, 180, 270):
        try:
            doc = fitz.open(str(src_path))
            page = doc[0]
            page.set_rotation(candidate)
            words = page.get_text("words")
            score = _keyword_hits(words)
            # Capture a small fingerprint of the actual result so it can
            # be compared across candidates afterward - if this is
            # IDENTICAL for every candidate, that directly confirms
            # set_rotation() isn't actually affecting extraction here.
            sample = tuple((w[4], round(w[0], 1), round(w[1], 1)) for w in words[:5])
            doc.close()
        except Exception:
            score = -1
            sample = None
        per_candidate.append((candidate, score, sample))
        if score > best_score:
            best_rotation, best_score = candidate, score
    if debug_log is not None:
        debug_log.append(f"    [DEBUG] find_best_rotation_setting candidates for {Path(src_path).name}:")
        for candidate, score, sample in per_candidate:
            debug_log.append(f"      /Rotate={candidate}: score={score} first-5-words-sample={sample}")
        identical = len({s for _, _, s in per_candidate if s is not None}) <= 1
        if identical:
            debug_log.append(
                "      -> ALL candidates produced an IDENTICAL word/coordinate sample. "
                "This confirms set_rotation() is NOT affecting get_text() here - the "
                "0deg 'winner' is an artifact of tie-breaking by iteration order, not a "
                "real detection. This function cannot currently distinguish the correct "
                "rotation and should not be trusted until fixed."
            )
    return best_rotation, best_score


def create_rotation_corrected_copy(src_path, out_path, debug_log=None):
    """NOT CURRENTLY USED - depends entirely on find_best_rotation_setting
    above, which is confirmed broken (see its docstring for the full
    account) and no longer called from the main pipeline. Kept only as a
    documented dead end.

    Originally: Creates a copy of src_path with every page's /Rotate flag set to
    the best-scoring orientation (see find_best_rotation_setting) - a
    pure metadata change via page.set_rotation(), no content re-rendering
    or re-embedding at all, unlike the earlier content-reconstruction
    attempt (normalize_page_rotation, still defined but no longer used)
    which ran into repeated clipping/CropBox bugs from physically
    rebuilding pages. Since the real page content and coordinate space
    are never touched, get_text()/get_drawings()/draw_rect() should all
    read and write consistently once the flag is corrected - no OCR, no
    separate readable-space/native-space bookkeeping needed at all.

    Returns (winning_rotation, keyword_score) on success, or (None,
    error_str) on failure.
    """
    try:
        best_rotation, score = find_best_rotation_setting(src_path, debug_log=debug_log)
        if score < MIN_ROTATION_CONFIDENCE_SCORE:
            # No real evidence for any particular orientation - leave the
            # file's own rotation untouched rather than guess. Returning
            # None here (not a rotation value) tells the caller nothing
            # was changed, distinct from an actual failure.
            return None, f"only {score} keyword match(es) found (need >= {MIN_ROTATION_CONFIDENCE_SCORE} to trust a correction) - left as-is"
        doc = fitz.open(str(src_path))
        for page in doc:
            page.set_rotation(best_rotation)
        doc.save(str(out_path))
        doc.close()
        return best_rotation, score
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def find_best_rotation_via_ocr(src_path, tesseract_exe, debug_log=None, dpi=300):
    """Tries each of the 4 possible /Rotate values (0/90/180/270), and for
    EACH candidate, RENDERS the page to an image and runs OCR on it,
    scoring by title-block keyword count (see _ORIENTATION_PROBE_KEYWORDS).

    This is the working replacement for find_best_rotation_setting above,
    which was confirmed broken by direct diagnostic evidence: text
    extraction (get_text) does not vary with /Rotate at all, since it
    reads the underlying content stream, which /Rotate never touches.

    Rendering DOES vary correctly with /Rotate - this is independently
    confirmed by the existing, working zero-extractable-text OCR fallback
    pipeline, which relies on exactly this same page.get_pixmap() default
    behavior. So trying each candidate, rendering it, and OCR'ing that
    render can actually distinguish a correct rotation from an incorrect
    one - unlike the old approach, which could not.

    Cost: this runs OCR up to 4 times per file (once per candidate),
    rather than the single cheap text-extraction call the old, broken
    version used. Only worth paying when a rotation correction is
    actually being considered - callers should still gate this behind
    page.rotation != 0 or similar, not run it unconditionally on every
    file.

    Returns (winning_rotation, keyword_score, diagnostic_or_None).
    """
    if ocr_fallback is None:
        return 0, -1, "OCR fallback module not loaded"
    if not tesseract_exe:
        return 0, -1, "no Tesseract-OCR install found"

    best_rotation, best_score = 0, -1
    per_candidate = []
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            for candidate in (0, 90, 180, 270):
                sub_dir = os.path.join(tmp_dir, f"rot_{candidate}")
                os.makedirs(sub_dir, exist_ok=True)
                try:
                    doc = fitz.open(str(src_path))
                    page = doc[0]
                    page.set_rotation(candidate)
                    image_path, scale = ocr_fallback.render_page_to_image(page, sub_dir, dpi=dpi)
                    doc.close()
                    rows = ocr_fallback.run_tesseract_tsv(image_path, tesseract_exe, sub_dir)
                    words = ocr_fallback.tsv_rows_to_word_tuples(rows, scale, min_confidence=15) if rows else []
                    score = _keyword_hits(words)
                except Exception as e:
                    score = -1
                    words = []
                per_candidate.append((candidate, score, len(words)))
                if score > best_score:
                    best_rotation, best_score = candidate, score
    except Exception as e:
        return 0, -1, f"unexpected error in rotation-via-OCR pipeline: {e}"

    if debug_log is not None:
        debug_log.append(f"    [DEBUG] find_best_rotation_via_ocr candidates for {Path(src_path).name}:")
        for candidate, score, word_count in per_candidate:
            debug_log.append(f"      /Rotate={candidate}: keyword_score={score} ({word_count} word(s) OCR'd)")

    return best_rotation, best_score, None


def create_rotation_corrected_copy_via_ocr(src_path, out_path, tesseract_exe, debug_log=None):
    """Creates a copy of src_path with every page's /Rotate flag set to
    the best-scoring orientation, using find_best_rotation_via_ocr (render
    + OCR based, confirmed to actually distinguish rotations - see that
    function's docstring). A pure /Rotate metadata change via
    page.set_rotation() on the SAVED COPY - no content re-rendering or
    re-embedding of the copy itself, same principle as the original
    (broken) create_rotation_corrected_copy this replaces.

    Returns (winning_rotation, keyword_score) on success, or (None,
    diagnostic_str) if no correction was applied (low confidence, no
    Tesseract, or an error) - the file's own rotation should be left
    untouched by the caller in that case.
    """
    try:
        best_rotation, score, diag = find_best_rotation_via_ocr(src_path, tesseract_exe, debug_log=debug_log)
        if diag is not None:
            return None, diag
        if score < MIN_ROTATION_CONFIDENCE_SCORE:
            return None, (
                f"only {score} keyword match(es) found via OCR at the best candidate "
                f"(need >= {MIN_ROTATION_CONFIDENCE_SCORE} to trust a correction) - left as-is"
            )
        doc = fitz.open(str(src_path))
        for page in doc:
            page.set_rotation(best_rotation)
        doc.save(str(out_path))
        doc.close()
        return best_rotation, score
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"



    """DEAD CODE - superseded, no longer called anywhere. Kept only as a
    documented dead end: this manually rotated the ALREADY-rendered image
    with Pillow after render_page_to_image had already produced it.

    Confirmed on a real drawing to be a genuine double-rotation bug:
    ocr_fallback.render_page_to_image() calls page.get_pixmap(matrix=...)
    with only a plain scaling matrix - no rotation handling of its own -
    and PyMuPDF's get_pixmap() automatically applies the page's own
    /Rotate flag by default. That means the rendered image was ALREADY
    correctly oriented before this function ever ran. The manual
    im.rotate(pil_angle, ...) step here then rotated that already-correct
    image a second time, producing a visibly wrong result even though the
    self-correcting keyword-match logic around it (see the removed
    ocr_extract_words_via_rotated_image) sometimes still found a handful
    of real words and looked like it was "working." A user directly
    confirmed a file that was originally correctly oriented came out
    rotated after this ran.

    Fixed by removing the manual rotation entirely and reusing the
    standard, already-correct ocr_fallback.ocr_extract_words() +
    ocr_fallback.OCRPageProxy() pipeline (the same one used for zero-
    extractable-text pages) for rotated pages too - see the call site in
    process this file's main loop. No PDF-specific coordinate math of our
    own is needed at all once the double-rotation is removed, since
    get_pixmap() already keeps the rendered image consistent with every
    other PyMuPDF coordinate operation on the same page.
    """
    raise NotImplementedError("superseded - see docstring")


def render_rotated_page_to_image(page, tmp_dir, dpi, rotate_matrix):
    """NOT CURRENTLY USED - part of an earlier, abandoned rotation-handling
    attempt (see _try_ocr_rotated_image above for how the later attempt
    that superseded this one was ALSO found to be wrong, and how it was
    fixed - by removing rotation-image handling entirely, since
    page.get_pixmap() already applies /Rotate correctly on its own). This
    produced 0 usable OCR words on a real test file - very plausibly a
    fitz.Matrix multiplication-order bug, though not confirmed - and
    there's no way to run PyMuPDF here to debug it further. Left in place
    in case that's ever worth revisiting.

    Like the render step in the OCR fallback module, but explicitly
    bakes the page's own rotation into the render matrix instead of
    leaving it out."""
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale) * rotate_matrix
    pix = page.get_pixmap(matrix=matrix)
    image_path = os.path.join(tmp_dir, "ocr_rotated_page.png")
    pix.save(image_path)
    return image_path, scale


def ocr_extract_words_rotated(page, tesseract_exe, rotation, dpi=300):
    """NOT CURRENTLY USED - see render_rotated_page_to_image above for
    why. Same overall pipeline as ocr_fallback.ocr_extract_words (render,
    run Tesseract, parse TSV into word tuples), reusing that module's
    Tesseract-running and TSV-parsing helpers directly - but with our own
    rotation-aware render step (render_rotated_page_to_image) instead of
    that module's plain scale-only one.

    Returns (words, diagnostic, inverse_rotate_matrix). `words` are in a
    landscape-normalized frame matching the rotated render.
    `inverse_rotate_matrix` (basic prerotate(-rotation), the exact
    opposite of the render rotation - simple to verify, not dependent on
    any PyMuPDF property semantics) converts a rect from that frame back
    to the real page's native coordinates, for drawing highlights."""
    rotate_matrix = fitz.Matrix(1, 1).prerotate(rotation)
    inverse_rotate_matrix = fitz.Matrix(1, 1).prerotate(-rotation)
    if ocr_fallback is None:
        return [], "OCR fallback module not loaded", inverse_rotate_matrix
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                image_path, scale = render_rotated_page_to_image(page, tmp_dir, dpi, rotate_matrix)
            except Exception as e:
                return [], f"failed to render rotated page to an image: {e}", inverse_rotate_matrix
            try:
                rows = ocr_fallback.run_tesseract_tsv(image_path, tesseract_exe, tmp_dir)
            except Exception as e:
                return [], f"tesseract subprocess failed: {e}", inverse_rotate_matrix
            if not rows:
                return [], "tesseract produced no output rows at all (empty TSV)", inverse_rotate_matrix
            words = ocr_fallback.tsv_rows_to_word_tuples(rows, scale)
            if not words:
                return [], "tesseract found no words at usable confidence", inverse_rotate_matrix
            return words, None, inverse_rotate_matrix
    except Exception as e:
        return [], f"unexpected error in rotated OCR pipeline: {e}", inverse_rotate_matrix


class RotatedOCRPageProxy:
    """NOT CURRENTLY USED - paired with the dormant matrix-based
    functions above. Like ocr_fallback.OCRPageProxy, but additionally
    maps drawing coordinates back to the real page's native (still-
    rotated) space via an explicit inverse rotation matrix. The new
    image-rotation approach doesn't need this - its word coordinates
    already land directly in native page space, so it reuses
    ocr_fallback.OCRPageProxy as-is, unchanged."""

    def __init__(self, real_page, ocr_words, inverse_rotate_matrix):
        self._real_page = real_page
        self._ocr_words = ocr_words
        self._inverse_rotate = inverse_rotate_matrix

    def get_text(self, kind="text"):
        if kind == "words":
            return self._ocr_words
        return self._real_page.get_text(kind)

    def new_shape(self):
        return _RotationAwareShape(self._real_page.new_shape(), self._inverse_rotate)

    def __getattr__(self, name):
        return getattr(self._real_page, name)


BOM_REGION_Y_PADDING_PT = 20.0
BOM_REGION_X_MARGIN_PT = 10.0


def find_bom_table_regions(page, words):
    """Bounding rect(s) for the real BOM table(s) on this page - reuses the
    same ITEM+QTY header detection and item-number column extraction as the
    BOM sequence check. X bounds derived from the actual header row words
    rather than page_width — previously using page_width caused the exclusion
    region to cover the full right half of the page, eating balloon candidates
    in the drawing body that happened to share the same X range as the BOM."""
    regions = []
    headers = find_bom_headers(words)
    page_width = page.rect.width
    for header in headers:
        col_words = extract_item_column(words, header)
        if not col_words:
            continue
        tops    = [w[1] for w in col_words] + [header[1]]
        bottoms = [w[3] for w in col_words] + [header[3]]
        y0 = min(tops) - BOM_REGION_Y_PADDING_PT
        y1 = max(bottoms) + BOM_REGION_Y_PADDING_PT
        x0 = header[0] - BOM_REGION_X_MARGIN_PT
        # Bound x1 to the rightmost word on the BOM header row rather than
        # the full page width. The MASS (EA) column header is typically the
        # rightmost cell — use its right edge plus a small margin.
        header_y_centre = (header[1] + header[3]) / 2
        header_row_words = [
            w for w in words
            if abs((w[1] + w[3]) / 2 - header_y_centre) <= HEADER_ROW_TOLERANCE_PT
        ]
        x1 = max((w[2] for w in header_row_words), default=page_width) + BOM_REGION_X_MARGIN_PT
        regions.append(fitz.Rect(x0, y0, x1, y1))
    return regions


def longest_monotonic_indices(values, decreasing=True):
    n = len(values)
    if n == 0:
        return []
    dp   = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            cond = (values[j] > values[i]) if decreasing else (values[j] < values[i])
            if cond and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
    best_i = max(range(n), key=lambda i: dp[i])
    backbone = []
    i = best_i
    while i != -1:
        backbone.append(i)
        i = prev[i]
    backbone.reverse()
    return backbone


def analyze_sequence(col_words):
    if len(col_words) < 3:
        return [], []

    values = [int(w[4].strip()) for w in col_words]
    desc_backbone = longest_monotonic_indices(values, decreasing=True)
    asc_backbone  = longest_monotonic_indices(values, decreasing=False)
    descending    = len(desc_backbone) >= len(asc_backbone)
    backbone      = desc_backbone if descending else asc_backbone
    backbone_set  = set(backbone)

    anomalies = [col_words[i] for i in range(len(col_words)) if i not in backbone_set]

    all_found = set(values)
    step = -1 if descending else 1
    missing_groups = []
    for bi, bj in zip(backbone, backbone[1:]):
        v_hi, v_lo = values[bi], values[bj]
        gap_values = []
        v = v_hi + step
        while v != v_lo:
            if v not in all_found:
                gap_values.append(v)
            v += step
        if gap_values:
            missing_groups.append({
                "values": gap_values,
                "hi_word": col_words[bi],
                "lo_word": col_words[bj],
            })

    return anomalies, missing_groups


def run_bom_sequence_check(page, page_num, report_lines, counts, ensure_page_header, balloons=None):
    words = page.get_text("words")
    headers = find_bom_headers(words)

    # Compute once here - always available regardless of whether headers were
    # found first-pass or via the OCR fallback path below.
    try:
        import SpellCheckOCR_Fallback_GROK as _ocr_fb
        is_ocr_page = isinstance(page, _ocr_fb.OCRPageProxy)
    except Exception:
        is_ocr_page = False

    if not headers:
        # No debug trail existed for this "found nothing" case before -
        # confirmed necessary on a rotated file where the header search
        # came back empty and the report showed literally no trace of the
        # BOM check having run at all, making it impossible to tell
        # whether ITEM/QTY/DESCRIPTION weren't found, or were found but
        # didn't align, or something else entirely. Report exactly what
        # was seen so the next run is diagnosable instead of another
        # guess.
        item_words = [w for w in words if w[4].strip() == "ITEM"]
        qty_words = [w for w in words if w[4].strip() == "QTY"]
        desc_words = [w for w in words if w[4].strip() == "DESCRIPTION"]
        report_lines.append(
            f"    [DEBUG] BOM header search on page {page_num + 1}: found "
            f"{len(item_words)} 'ITEM' word(s), {len(qty_words)} 'QTY' word(s), "
            f"{len(desc_words)} 'DESCRIPTION' word(s) - no row had all three "
            f"aligned within {HEADER_ROW_TOLERANCE_PT}pt, so no BOM table header "
            f"was found."
        )
        for label, ws in (("ITEM", item_words), ("QTY", qty_words), ("DESCRIPTION", desc_words)):
            for w in ws:
                report_lines.append(f"      {label} at ({w[0]:.1f},{w[1]:.1f})-({w[2]:.1f},{w[3]:.1f})")

        # If ITEM was found but QTY wasn't, dump every word OCR actually
        # read near each ITEM instance - shows directly whether QTY got
        # misread as garbled text nearby (an OCR accuracy problem on
        # small/cramped table text, different fix than an orientation
        # problem) or whether that whole area came back essentially
        # blank (a different problem again - e.g. DPI too low to resolve
        # small text after rotation).
        NEARBY_RADIUS_PT = 60.0

        def _dump_nearby(label, w):
            wcx, wcy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
            nearby = [
                other for other in words
                if other is not w
                and abs((other[0] + other[2]) / 2 - wcx) <= NEARBY_RADIUS_PT
                and abs((other[1] + other[3]) / 2 - wcy) <= NEARBY_RADIUS_PT
            ]
            nearby.sort(key=lambda o: ((o[1] + o[3]) / 2, (o[0] + o[2]) / 2))
            report_lines.append(
                f"      [DEBUG] every word OCR read within {NEARBY_RADIUS_PT:.0f}pt of "
                f"{label} at ({w[0]:.1f},{w[1]:.1f}):"
            )
            if not nearby:
                report_lines.append("        (none - this area came back essentially blank)")
            for other in nearby:
                report_lines.append(f"        '{other[4]}' at ({other[0]:.1f},{other[1]:.1f})-({other[2]:.1f},{other[3]:.1f})")

        if item_words and not qty_words:
            for iw in item_words:
                _dump_nearby("ITEM", iw)

        # Confirmed necessary on a real file: QTY and DESCRIPTION were
        # found perfectly aligned with each other (Y-centers within a
        # fraction of a point), meaning the real header row WAS located -
        # but neither found ITEM instance was anywhere near that row, so
        # ITEM was either misread as different text at that exact spot or
        # never recognized there at all. Dumping words near QTY/
        # DESCRIPTION directly (rather than only near ITEM) shows which.
        if qty_words or desc_words:
            for label, ws in (("QTY", qty_words), ("DESCRIPTION", desc_words)):
                for w in ws:
                    _dump_nearby(label, w)

        # Both found ITEM instances sit to the RIGHT of QTY, when ITEM
        # (the leftmost BOM column, by this company's convention) should
        # be to QTY's LEFT - meaning neither is the real header, and the
        # 60pt-radius dumps above may simply not reach far enough left to
        # show what's actually there. This dumps EVERYTHING on the same
        # row as QTY, full page width, no radius limit - a direct answer
        # to "is there anything at all where ITEM should be on this row"
        # rather than another guess at how wide a search radius to use.
        if qty_words:
            qw = qty_words[0]
            qcy = (qw[1] + qw[3]) / 2
            same_row = [
                w for w in words
                if abs((w[1] + w[3]) / 2 - qcy) <= HEADER_ROW_TOLERANCE_PT * 3
            ]
            same_row.sort(key=lambda w: w[0])
            report_lines.append(
                f"      [DEBUG] every word OCR read on the same row as QTY "
                f"(y-center {qcy:.1f} +/-{HEADER_ROW_TOLERANCE_PT * 3:.0f}pt), full page width:"
            )
            for w in same_row:
                report_lines.append(f"        '{w[4]}' at ({w[0]:.1f},{w[1]:.1f})-({w[2]:.1f},{w[3]:.1f})")

        # Fallback to the QTY+DESCRIPTION-only match, restricted to
        # OCR-sourced pages specifically - direct text extraction is
        # reliable enough that ITEM+QTY+DESCRIPTION should always be
        # findable together there, so this stays off for normal pages
        # rather than loosening validation everywhere.
        if is_ocr_page and not headers:
            headers = find_bom_headers_relaxed(words)
            if headers:
                report_lines.append(
                    "    [DEBUG] No exact 'ITEM' text was read by OCR, but QTY and "
                    "DESCRIPTION were found aligned on the same row - treating that as "
                    "a confirmed BOM header (ITEM column position below is estimated, "
                    "not read directly)."
                )

    # OCR words arrive in *visual* (screen/rendered) coordinates, but
    # PyMuPDF drawing operations (new_shape, insert_text) use the page's
    # *native* PDF coordinate space.  For pages with /Rotate != 0 these two
    # spaces differ; applying the derotation_matrix converts visual → native
    # so highlights and labels land on the correct visual position.
    # Non-rotated pages have an identity-like derot, so the helpers are
    # always safe to call.
    _real_bom_page = getattr(page, '_real_page', page)
    _derot_bom = _real_bom_page.derotation_matrix if _real_bom_page.rotation != 0 else None

    def _bom_native_rect(word):
        """word tuple → fitz.Rect in native (drawing) coordinates."""
        r = fitz.Rect(word[0], word[1], word[2], word[3])
        if _derot_bom is None:
            return r
        pts = [fitz.Point(r.x0, r.y0) * _derot_bom,
               fitz.Point(r.x1, r.y0) * _derot_bom,
               fitz.Point(r.x0, r.y1) * _derot_bom,
               fitz.Point(r.x1, r.y1) * _derot_bom]
        return fitz.Rect(min(p.x for p in pts), min(p.y for p in pts),
                         max(p.x for p in pts), max(p.y for p in pts))

    def _bom_native_pt(x, y):
        """Visual (x, y) → native fitz.Point."""
        if _derot_bom is None:
            return fitz.Point(x, y)
        return fitz.Point(x, y) * _derot_bom

    # Track y-positions of already-placed BOM margin labels so consecutive
    # findings are spread apart and never overprint each other.
    _bom_label_ys = []

    def _claim_label_y(desired_y):
        """Return a y-position >= BOM_LABEL_MIN_SPACING_PT from every
        previously claimed y.  Searches outward from desired_y in
        BOM_LABEL_MIN_SPACING_PT steps (up first, then down)."""
        step = BOM_LABEL_MIN_SPACING_PT
        for offset in [0, -step, step, -2 * step, 2 * step,
                       -3 * step, 3 * step, -4 * step, 4 * step]:
            candidate = desired_y + offset
            if all(abs(candidate - used) >= step for used in _bom_label_ys):
                _bom_label_ys.append(candidate)
                return candidate
        # Fallback: accept desired_y even if crowded.
        _bom_label_ys.append(desired_y)
        return desired_y

    for header in headers:
        col_words = extract_item_column(words, header)
        if len(col_words) < 3:
            continue

        values = [w[4].strip() for w in col_words]
        report_lines.append(
            f"  Page {page_num + 1}, BOM table near ({header[0]:.1f},{header[1]:.1f}): "
            f"{len(col_words)} item row(s): {', '.join(values)}"
        )

        anomalies, missing_groups = analyze_sequence(col_words)

        # Check every BOM item number has at least one matching balloon on
        # the drawing. Runs regardless of sequence result - a clean sequence
        # doesn't mean every item has a balloon on the drawing.
        # Guard: only run the no-balloon check when reliable text is available.
        # Two conditions must both be true:
        #   1. balloons is truthy  - find_balloon_numbers found at least one
        #      balloon; an empty list means detection found nothing (SHX page
        #      with all-vector balloon text) so skip rather than false-flag all.
        #   2. not is_ocr_page - when the BOM text came from OCR (rotated page
        #      or full SHX fallback), OCR word coordinates don't align reliably
        #      with the vector geometry used by find_balloon_numbers, so even a
        #      non-empty balloon list would produce false positives for items
        #      whose balloon numbers are SHX-rendered and therefore invisible to
        #      the real text extraction that balloon detection depends on.
        if balloons and not is_ocr_page:
            balloon_numbers = set()
            for b in balloons:
                try:
                    balloon_numbers.add(int(b["text"].strip()))
                except ValueError:
                    pass
            for item_word in col_words:
                try:
                    item_num = int(item_word[4].strip())
                except ValueError:
                    continue
                if item_num not in balloon_numbers:
                    counts["bom_no_balloon"] += 1
                    ensure_page_header()
                    print(f"  Page {page_num + 1}: BOM item {item_num} has no matching balloon on drawing")
                    report_lines.append(
                        f"    [BOM NO BALLOON] item {item_num} in BOM but no matching balloon found on drawing"
                    )
                    rect = _bom_native_rect(item_word)
                    draw_highlight(page, rect)
                    # Draw a bold red "?" to the left of the ITEM column -
                    # same position and style as the missing-sequence label.
                    try:
                        lbl_y = _claim_label_y(item_word[3] - 1)
                        page.insert_text(
                            _bom_native_pt(item_word[0] - BOM_LABEL_OFFSET_X_PT, lbl_y), "?",
                            fontsize=14, fontname="hebo", color=HIGHLIGHT_COLOR,
                        )
                    except Exception:
                        pass

        if not anomalies and not missing_groups:
            report_lines.append("    Sequence OK.")
            continue

        if anomalies:
            counts["bom_out_of_seq"] += len(anomalies)
            ensure_page_header()
            anomaly_texts = [a[4].strip() for a in anomalies]
            print(f"  Page {page_num + 1}: out-of-sequence item number(s): {', '.join(anomaly_texts)}")
            report_lines.append(f"    OUT OF SEQUENCE: {', '.join(anomaly_texts)}")
            for a in anomalies:
                rect = _bom_native_rect(a)
                draw_highlight(page, rect)

        if missing_groups:
            counts["bom_missing"] += sum(len(g["values"]) for g in missing_groups)
            ensure_page_header()
            for g in missing_groups:
                hi, lo = g["hi_word"], g["lo_word"]
                missing_texts = ", ".join(str(v) for v in g["values"])
                print(f"  Page {page_num + 1}: missing item number(s) {missing_texts} "
                      f"(between {hi[4].strip()} and {lo[4].strip()})")
                report_lines.append(
                    f"    MISSING: {missing_texts}  (between rows '{hi[4].strip()}' and '{lo[4].strip()}')"
                )
                for bracket_word in ():  # no row highlight - the text label is sufficient
                    rect = fitz.Rect(bracket_word[0], bracket_word[1], bracket_word[2], bracket_word[3])
                    draw_highlight(page, rect)

                # Draw a red "3?" / "3,4?" label just to the left of the
                # ITEM column, vertically centred in the gap between the
                # two bracketing rows. This makes the missing number(s)
                # immediately obvious without needing to read the report.
                label_text = ", ".join(f"{v}?" for v in g["values"])
                gap_y = (hi[3] + lo[1]) / 2   # midpoint between hi bottom and lo top
                label_x = hi[0] - BOM_LABEL_OFFSET_X_PT   # to the left of the ITEM column
                label_y = _claim_label_y(max(gap_y, hi[3]))
                try:
                    page.insert_text(
                        _bom_native_pt(label_x, label_y), label_text,
                        fontsize=14, fontname="hebo", color=HIGHLIGHT_COLOR,
                    )
                except Exception as e:
                    report_lines.append(f"    (could not insert missing-item label: {e})")


# ==================================================================
# CHECK 3: project number consistency
# ==================================================================

def leading_letters(token):
    m = re.match(r"^[A-Za-z]+", token)
    return m.group() if m else ""


def get_reference_project_number(pdf_path):
    stem = Path(pdf_path).stem
    return stem.split("-", 1)[0]


def find_project_number_mismatches(page, reference, words=None):
    ref_prefix = leading_letters(reference).upper()
    ref_len    = len(reference)
    if not ref_prefix or ref_len == 0:
        return []

    if words is None:
        words = page.get_text("words")
    flagged = []
    for w in words:
        text = w[4].strip()
        if not text:
            continue
        for sub in text.split("-"):
            if not sub:
                continue
            if leading_letters(sub).upper() == ref_prefix and len(sub) == ref_len:
                if sub.upper() != reference.upper():
                    flagged.append((w, sub))
                    break
    return flagged


def run_project_number_check(page, page_num, reference, report_lines, counts, ensure_page_header, words=None):
    flags = find_project_number_mismatches(page, reference, words=words)
    if not flags:
        return

    counts["project_number"] += len(flags)
    ensure_page_header()
    for w, sub in flags:
        print(f"  Page {page_num + 1}: found '{sub}' (expected '{reference}') in word '{w[4].strip()}'")
        report_lines.append(
            f"    [PROJECT NUMBER] '{sub}' (expected '{reference}')  "
            f"in word '{w[4].strip()}'  at ({w[0]:.1f},{w[1]:.1f})"
        )
        rect = fitz.Rect(w[0], w[1], w[2], w[3])
        draw_highlight(page, rect, label=reference,
                       label_color=HIGHLIGHT_COLOR, label_fontsize=6.72,
                       label_offset_lines=1.0)


# ==================================================================
# CHECK 3b: drawing number in title block vs PDF filename
# ==================================================================
# The existing project-number check (above) verifies that the PJ#####
# prefix appearing in drawing number tokens across the page matches the
# filename prefix. But it WON'T catch a wrong FULL drawing number - e.g.
# a file named PJ00193-GTA-3420-6-000416.pdf whose title block still
# shows PJ00193-GTA-3420-6-000415 from a previous revision. This check
# finds the actual drawing number field in the title block and compares
# it to the full filename stem.

def find_drawing_number_in_titleblock(words, ref_stem, page_width, page_height):
    """Return the word tuple for the drawing number in the title block,
    or None if nothing suitable is found.

    Strategy — bottommost-wins:
      The title block is always the lowest element on the page.  Any
      drawing references in notes text sit higher up (smaller Y).  So
      among all hyphenated tokens with the right project prefix that fall
      in the broad bottom-right corner, the one with the LARGEST Y value
      (lowest on the page) is the title block number.  No label-anchor
      needed — the vertical ordering does the disambiguation reliably on
      any sheet size.

    Corner is defined by CORNER_X_FRACTION (x) and CORNER_Y_FRACTION (y).
    The x threshold is relaxed slightly (×0.8) so the drawing number cell
    isn't accidentally clipped on sheets where the title block starts a
    bit left of the usual 55 % mark."""
    if not ref_stem:
        return None
    ref_prefix = leading_letters(ref_stem.split("-")[0]).upper()
    if not ref_prefix:
        return None

    # Relaxed X threshold so we don't clip the title block on wider layouts.
    cx0 = page_width  * CORNER_X_FRACTION * 0.8
    cy0 = page_height * CORNER_Y_FRACTION
    corner_words = [w for w in words if w[0] >= cx0 and w[1] >= cy0]

    # All hyphenated tokens whose first segment starts with the project prefix.
    candidates = [
        w for w in corner_words
        if "-" in w[4] and w[4].strip()
        and leading_letters(w[4].strip().split("-")[0]).upper() == ref_prefix
    ]
    if not candidates:
        return None

    # The title block drawing number is the lowest on the page (largest Y).
    # Notes drawing references are always higher up.
    candidates.sort(key=lambda w: w[1], reverse=True)
    return candidates[0]


def run_drawing_number_check(page, page_num, ref_stem, report_lines, counts, ensure_page_header, words=None):
    """Flag if the drawing number in the title block doesn't match the
    PDF filename stem (minus extension)."""
    if not ref_stem:
        return
    if words is None:
        words = page.get_text("words")
    pw, ph = page.rect.width, page.rect.height
    found = find_drawing_number_in_titleblock(words, ref_stem, pw, ph)
    if found is None:
        return  # couldn't locate a drawing-number candidate - skip silently
    found_text = found[4].strip()
    if found_text.upper() in ref_stem.upper():
        return  # drawing number is contained in the filename - all good
    counts["project_number"] += 1
    ensure_page_header()
    print(f"  Page {page_num + 1}: drawing number '{found_text}' doesn't match filename '{ref_stem}'")
    report_lines.append(
        f"    [DRAWING NUMBER] title block shows '{found_text}' but filename is '{ref_stem}'  "
        f"at ({found[0]:.1f},{found[1]:.1f})"
    )
    rect = fitz.Rect(found[0], found[1], found[2], found[3])
    # Derive the "correct" drawing number from the filename stem, stripping
    # any revision/issue suffix that follows an underscore (e.g. _0a,
    # _Rev0_ISSUED) — the drawing number itself uses only hyphens.
    correct_dwg = ref_stem.split("_")[0]
    _lfs_dwg = 10.22
    draw_highlight(page, rect, label=correct_dwg,
                   label_color=HIGHLIGHT_COLOR, label_fontsize=_lfs_dwg,
                   label_offset_lines=1.0)
    # Second label line: clarify the check type
    _note_y = min(rect.y1 + _lfs_dwg * 1.5, page.rect.y1 - 2.0)
    _note_x = max(rect.x0, page.rect.x0 + 1.0)
    page.insert_text(
        (_note_x, _note_y),
        "CHECK PDF NAME",
        fontsize=6.72,
        fontname="helv",
        color=HIGHLIGHT_COLOR,
    )


# ==================================================================
# CHECK 4: revision stamp (REV letter/number vs PRELIMINARY/APPROVED stamp)
# ==================================================================

def find_rev_header(page, words, debug_log=None):
    """The real title-block REV header - identified by POSITION (bottom-
    right corner of the page), not by pairing with a neighbouring word.
    SCALE-pairing proved unreliable on real drawings."""
    pw, ph = page.rect.width, page.rect.height
    cx0, cy0 = pw * CORNER_X_FRACTION, ph * CORNER_Y_FRACTION

    corner_words = [w for w in words if w[0] >= cx0 and w[1] >= cy0]
    exact_rev = [w for w in corner_words if w[4].strip().upper() == "REV"]
    rev_candidates = exact_rev if exact_rev else [w for w in corner_words if "REV" in w[4].strip().upper()]

    if debug_log is not None:
        debug_log.append(
            f"    [DEBUG] page size {pw:.1f}x{ph:.1f}, corner region x>={cx0:.1f} y>={cy0:.1f}"
        )
        debug_log.append(f"    [DEBUG] 'REV' candidate(s) in corner: {len(rev_candidates)}")
        for r in rev_candidates:
            debug_log.append(f"      '{r[4]}' at ({r[0]:.1f},{r[1]:.1f})")

    if not rev_candidates:
        return None
    return max(rev_candidates, key=lambda w: w[0] + w[1])


def find_rev_value_below(words, header):
    """The value below a REV header - compares VERTICAL CENTERS, not
    edges, since the value is usually a much bigger font than the header
    label and its box can start above the header's own bottom edge."""
    hx0, hx1 = header[0], header[2]
    header_center_y = (header[1] + header[3]) / 2
    candidates = [
        w for w in words
        if hx0 - 3 <= w[0] <= hx1 + 3 and (w[1] + w[3]) / 2 > header_center_y
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda w: (w[1] + w[3]) / 2)
    return candidates[0]


def classify_rev(value_word):
    text = value_word[4].strip()
    if re.fullmatch(r"\d+", text):
        return "numeric"
    if re.fullmatch(r"[A-Za-z]+", text):
        return "alpha"
    return None


def find_stamp_evidence(words, anchor_text, companions, debug_log=None):
    """Find occurrences of anchor_text, confirmed by checking that ALL
    companion words appear nearby (spatial proximity). Matches by
    SUBSTRING, not exact equality, and with no font-size filtering - both
    proved necessary against real drawing data."""
    anchors = [w for w in words if anchor_text in w[4].strip().upper()]
    if debug_log is not None:
        debug_log.append(f"    [DEBUG] words containing '{anchor_text}': {len(anchors)}")
        for w in anchors:
            debug_log.append(f"      '{w[4]}' at ({w[0]:.1f},{w[1]:.1f})")

    results = []
    for a in anchors:
        ax0, ay0, ax1, ay1 = a[0], a[1], a[2], a[3]
        margin = max(STAMP_SEARCH_MARGIN, (ay1 - ay0) * STAMP_SEARCH_MARGIN_HEIGHT_MULT)
        rx0, rx1 = ax0 - margin, ax1 + margin
        ry0, ry1 = ay0 - 5, ay1 + margin

        nearby = [w for w in words if rx0 <= w[0] <= rx1 and ry0 <= w[1] <= ry1]
        nearby_text = " ".join(w[4].strip().upper() for w in nearby)
        matched = [a] + [w for w in nearby if any(c in w[4].strip().upper() for c in companions)]

        if debug_log is not None:
            missing = [c for c in companions if c not in nearby_text]
            if missing:
                debug_log.append(
                    f"      '{a[4]}' at ({ax0:.1f},{ay0:.1f}): "
                    f"missing companion word(s) {missing} within {margin:.1f}pt -> rejected "
                    f"(nearby text found: {nearby_text!r})"
                )

        if all(c in nearby_text for c in companions):
            results.append((a, matched))
    return results


def words_union_rect(word_list):
    x0 = min(w[0] for w in word_list)
    y0 = min(w[1] for w in word_list)
    x1 = max(w[2] for w in word_list)
    y1 = max(w[3] for w in word_list)
    return fitz.Rect(x0, y0, x1, y1)


def run_revision_stamp_check(page, page_num, report_lines, counts, ensure_page_header):
    words = page.get_text("words")

    debug_log = []
    header = find_rev_header(page, words, debug_log=debug_log)
    report_lines.extend(debug_log)

    if header is None:
        report_lines.append(f"  Page {page_num + 1}: No title-block REV header found in the corner region.")
        return

    value = find_rev_value_below(words, header)
    if value is None:
        report_lines.append(
            f"  Page {page_num + 1}: REV header found at "
            f"({header[0]:.1f},{header[1]:.1f}) but no value word below it - skipped."
        )
        return

    classification = classify_rev(value)
    rev_text = value[4].strip()
    if classification is None:
        report_lines.append(
            f"  Page {page_num + 1}: REV value '{rev_text}' is neither numeric nor alphabetic - skipped."
        )
        return

    stamp_debug = []
    approved_hits = find_stamp_evidence(words, "APPROVED", ["FOR", "CONSTRUCTION"], debug_log=stamp_debug)
    prelim_hits   = find_stamp_evidence(words, "PRELIMINARY", ["NOT", "FOR", "CONSTRUCTION"], debug_log=stamp_debug)
    report_lines.extend(stamp_debug)
    has_approved  = len(approved_hits) > 0
    has_prelim    = len(prelim_hits) > 0

    # Raw counts (anchor word present anywhere on the page at all, whether
    # or not its companions could be confirmed nearby) - used below to
    # tell "the stamp genuinely isn't there" apart from "the stamp is
    # there but this check can't confirm its layout" (e.g. a file from a
    # different export pipeline that spaces/renders the stamp differently
    # - confirmed on real files). Per direction: only the first case is a
    # real finding worth failing the drawing over.
    approved_raw_count = sum(1 for w in words if "APPROVED" in w[4].strip().upper())
    prelim_raw_count   = sum(1 for w in words if "PRELIMINARY" in w[4].strip().upper())

    expects = "preliminary" if classification == "alpha" else "approved"
    report_lines.append(
        f"  Page {page_num + 1}: REV = '{rev_text}' ({classification}) -> expects "
        f"{'PRELIMINARY ONLY / NOT FOR CONSTRUCTION' if expects == 'preliminary' else 'APPROVED FOR CONSTRUCTION'} stamp. "
        f"Found: approved={has_approved}, preliminary={has_prelim}"
    )

    if has_approved and has_prelim:
        counts["rev_stamp_conflict"] += 1
        ensure_page_header()
        print(f"  Page {page_num + 1}: BOTH stamps present (conflicting) - REV is '{rev_text}'")
        report_lines.append("    CONFLICT: both APPROVED and PRELIMINARY stamps found on the same drawing")
        for _, matched in approved_hits + prelim_hits:
            draw_highlight(page, words_union_rect(matched), enlarge=False)
        return

    correct = (expects == "preliminary" and has_prelim) or (expects == "approved" and has_approved)
    if correct:
        return

    wrong_hits = approved_hits if expects == "preliminary" else prelim_hits
    ensure_page_header()

    if wrong_hits:
        counts["rev_stamp_wrong"] += 1
        wrong_name = "APPROVED FOR CONSTRUCTION" if expects == "preliminary" else "PRELIMINARY ONLY"
        print(f"  Page {page_num + 1}: REV '{rev_text}' expects the other stamp but found '{wrong_name}' instead")
        report_lines.append(f"    WRONG STAMP: found '{wrong_name}' but REV '{rev_text}' expects the other one")
        for _, matched in wrong_hits:
            draw_highlight(page, words_union_rect(matched), enlarge=False)
    else:
        raw_count = approved_raw_count if expects == "approved" else prelim_raw_count
        wanted_word = "APPROVED" if expects == "approved" else "PRELIMINARY"
        if raw_count > 0:
            # The word itself is on the page somewhere, so a stamp likely
            # exists - this check just couldn't confirm its layout (e.g.
            # companions too far away, or split across an image/vector
            # element). Per direction: don't fail or highlight when this
            # check can't interpret the stamp, just say so plainly.
            report_lines.append(
                f"    STAMP NOT CONFIRMED (not flagged): REV '{rev_text}' expects a "
                f"{'APPROVED FOR CONSTRUCTION' if expects == 'approved' else 'PRELIMINARY ONLY'} stamp - "
                f"'{wanted_word}' text was found on the page but this check could not confirm its "
                f"full layout, so it's being skipped rather than treated as an error."
            )
        else:
            counts["rev_stamp_missing"] += 1
            print(f"  Page {page_num + 1}: REV '{rev_text}' expects a stamp but none was found")
            report_lines.append(f"    MISSING STAMP: REV '{rev_text}' expects a stamp but none was found on the page")
            draw_highlight(page, fitz.Rect(value[0], value[1], value[2], value[3]))


# ==================================================================
# CHECK 5: REV compare (corner REV vs revisions-table REV)
# ==================================================================

def find_revisions_table_headers(words):
    """Find the revisions table's header row - identified by 'REV' having
    both 'BY' and 'DATE' on the same row nearby. Also returns 'CHECKED' on
    that row if present, needed to work out the DESCRIPTION column's
    boundary (which does NOT align with the DESCRIPTION header label's own
    position - confirmed against real data: header sits centred well to
    the right of where the actual value text starts)."""
    rev_words     = [w for w in words if w[4].strip().upper() == "REV"]
    by_words      = [w for w in words if w[4].strip().upper() == "BY"]
    date_words    = [w for w in words if w[4].strip().upper() == "DATE"]
    checked_words = [w for w in words if w[4].strip().upper() == "CHECKED"]

    for r in rev_words:
        ry = (r[1] + r[3]) / 2
        by_match   = next((b for b in by_words if abs((b[1]+b[3])/2 - ry) <= TABLE_ROW_TOLERANCE_PT), None)
        date_match = next((d for d in date_words if abs((d[1]+d[3])/2 - ry) <= TABLE_ROW_TOLERANCE_PT), None)
        if by_match and date_match:
            checked_match = next((c for c in checked_words if abs((c[1]+c[3])/2 - ry) <= TABLE_ROW_TOLERANCE_PT), None)
            return {"rev": r, "by": by_match, "date": date_match, "checked": checked_match}
    return None


def find_table_rev_value(words):
    """Revisions history table REV - identified by 'BY' and 'DATE' on the
    same row, value ABOVE the header (inverted layout vs the corner).
    When multiple revisions are listed, each new one is added above the
    previous (the row closest to the header is the OLDEST, not the
    latest) - confirmed on a real drawing: REV B (newer date) sat above
    REV A (older date), with A directly above the header. So the correct
    "current" revision is the TOPMOST *filled* row, not the closest one -
    but "topmost in this column's x-range anywhere on the page" is too
    broad: confirmed a real file has unrelated text (e.g. a note) far up
    the page that happens to share the REV column's x-range by
    coincidence. Instead, start from the row closest to the header
    (guaranteed to be real, since that's always where revision entries
    begin) and walk upward only while each next row is spaced similarly
    to real table rows - stopping the moment a gap suggests we've left
    the filled part of the table.
    """
    headers = find_revisions_table_headers(words)
    if headers is None:
        return None, None
    header = headers["rev"]

    hx0, hx1 = header[0], header[2]
    header_cy = (header[1] + header[3]) / 2
    above = [w for w in words if hx0 - 3 <= w[0] <= hx1 + 3 and (w[1] + w[3]) / 2 < header_cy]
    if not above:
        return header, None
    above.sort(key=lambda w: -(w[1] + w[3]) / 2)  # closest-to-header first - always correct as a starting point

    latest = above[0]
    prev_cy = (above[0][1] + above[0][3]) / 2
    first_row_gap = header_cy - prev_cy
    max_row_gap = max(first_row_gap * 1.8, first_row_gap + 10)
    for w in above[1:]:
        cy = (w[1] + w[3]) / 2
        if prev_cy - cy > max_row_gap:
            break
        latest = w
        prev_cy = cy
    return header, latest


def run_rev_compare_check(page, page_num, report_lines, counts, ensure_page_header):
    words = page.get_text("words")

    corner_header = find_rev_header(page, words)
    corner_value  = find_rev_value_below(words, corner_header) if corner_header else None
    table_header, table_value = find_table_rev_value(words)

    if corner_header:
        report_lines.append(
            f"  Page {page_num + 1}: corner REV = "
            f"'{corner_value[4].strip() if corner_value else '?'}'"
        )
    if table_header:
        report_lines.append(
            f"  Page {page_num + 1}: revisions-table REV = "
            f"'{table_value[4].strip() if table_value else '?'}'"
        )

    if corner_value and table_value:
        cv = corner_value[4].strip().upper()
        tv = table_value[4].strip().upper()
        if cv == tv:
            report_lines.append(f"    -> MATCH ('{cv}' == '{tv}')")
        else:
            counts["rev_compare_mismatch"] += 1
            ensure_page_header()
            print(f"  Page {page_num + 1}: REV MISMATCH - corner='{cv}' table='{tv}'")
            report_lines.append(f"    [REV COMPARE] MISMATCH: corner='{cv}' vs table='{tv}'")
            draw_highlight(page, fitz.Rect(*corner_value[:4]))
            draw_highlight(page, fitz.Rect(*table_value[:4]))
    elif corner_value or table_value:
        # Only one side could be located at all - this isn't a genuine
        # mismatch (that requires seeing BOTH values and finding them
        # different), it's this check failing to interpret one side.
        # Per direction: don't fail or highlight when the check can't
        # interpret the text, just say so plainly.
        report_lines.append(
            "    [REV COMPARE] Could not compare (one side missing) - not flagged as a mismatch"
        )


# ==================================================================
# CHECK 6: revisions-table DESCRIPTION vs corner REV letter/number
# ==================================================================

def find_table_description_value(words, headers, ref_row_y):
    """The revisions table's DESCRIPTION value text on the same row as
    ref_row_y. Column boundary comes from the neighbouring DATE and
    CHECKED headers (right edge of DATE to left edge of CHECKED) - NOT
    from the DESCRIPTION header's own position, which sits centred well to
    the right of where the value text actually starts (confirmed against
    real data)."""
    date_header    = headers.get("date")
    checked_header = headers.get("checked")
    if date_header is None or checked_header is None:
        return "", []

    x0, x1 = date_header[2], checked_header[0]
    row_words = [w for w in words if x0 <= w[0] <= x1 and abs((w[1] + w[3]) / 2 - ref_row_y) < 2]
    row_words.sort(key=lambda w: w[0])
    phrase = " ".join(w[4].strip() for w in row_words).upper()
    return phrase, row_words


def run_rev_description_check(page, page_num, report_lines, counts, ensure_page_header):
    words = page.get_text("words")

    # The CORNER REV drives the classification (per spec) - not the
    # table's own REV value, which can legitimately differ (that's what
    # the separate REV-compare check is for). Confirmed bug: a real test
    # file had corner REV='A' but table REV='0' + 'ISSUED FOR
    # CONSTRUCTION' - classifying off the table's own REV missed it
    # entirely since '0'+'CONSTRUCTION' is a correct pairing on its own.
    corner_header = find_rev_header(page, words)
    corner_value  = find_rev_value_below(words, corner_header) if corner_header else None
    if corner_value is None:
        return
    classification = classify_rev(corner_value)
    if classification is None:
        return

    # Still need the table's own current-row position (via its REV/BY/DATE
    # header pairing) purely to know WHICH row's DESCRIPTION to read.
    # Same walk-upward-with-spacing-tolerance rule as find_table_rev_value.
    headers = find_revisions_table_headers(words)
    if headers is None:
        return

    rev_header = headers["rev"]
    hx0, hx1 = rev_header[0], rev_header[2]
    header_cy = (rev_header[1] + rev_header[3]) / 2
    above = [w for w in words if hx0 - 3 <= w[0] <= hx1 + 3 and (w[1] + w[3]) / 2 < header_cy]
    table_row_ref = None
    if above:
        above.sort(key=lambda w: -(w[1] + w[3]) / 2)
        table_row_ref = above[0]
        prev_cy = (above[0][1] + above[0][3]) / 2
        first_row_gap = header_cy - prev_cy
        max_row_gap = max(first_row_gap * 1.8, first_row_gap + 10)
        for w in above[1:]:
            cy = (w[1] + w[3]) / 2
            if prev_cy - cy > max_row_gap:
                break
            table_row_ref = w
            prev_cy = cy
    if table_row_ref is None:
        return

    ref_row_y = (table_row_ref[1] + table_row_ref[3]) / 2
    phrase, desc_words = find_table_description_value(words, headers, ref_row_y)
    if not desc_words:
        return  # empty description cell - nothing to check

    report_lines.append(
        f"  Page {page_num + 1}: corner REV = '{corner_value[4].strip()}' ({classification}), "
        f"table DESCRIPTION = '{phrase}'"
    )

    mismatch = (
        (classification == "alpha" and "ISSUED FOR CONSTRUCTION" in phrase) or
        (classification == "numeric" and "ISSUED FOR REVIEW" in phrase)
    )
    if not mismatch:
        return  # correct pairing, or unrelated wording - ignore per spec

    counts["rev_description_mismatch"] += 1
    ensure_page_header()
    print(f"  Page {page_num + 1}: DESCRIPTION '{phrase}' doesn't match corner REV "
          f"'{corner_value[4].strip()}' ({classification})")
    report_lines.append(
        f"    [DESCRIPTION MISMATCH] '{phrase}' doesn't match corner REV "
        f"'{corner_value[4].strip()}' ({classification})"
    )
    draw_highlight(page, words_union_rect(desc_words), enlarge=False)


# ==================================================================
# CHECK 7: detail-view ITEM reference number length (must be 6 digits)
# ==================================================================

# Margin (points) for locating "SCALE" below a detail-view "ITEM" label,
# and how many digits a candidate reference number must have to be
# considered real (rules out the 1-3 digit scale ratio denominator, e.g.
# "1:20", while still catching truncated reference numbers like 4-5 digits)
ITEM_SCALE_X_MARGIN = 30.0
ITEM_SCALE_Y_MARGIN = 25.0
ITEM_REF_MIN_DIGITS = 4
# How far (points) from the ITEM label the reference number itself can be.
# Deliberately looser than ITEM_SCALE_X_MARGIN (the ratio sits right next
# to "ITEM", but the reference number can trail a bit further after the
# ratio on the same line) - but still a real, page-relative bound.
ITEM_REF_X_MARGIN = 150.0
ITEM_REF_EXPECTED_DIGITS = 6


def find_detail_view_items(words):
    """Standalone 'ITEM' labels used in detail-view callouts (e.g.
    'ITEM 1 / SCALE 1:20 / 000130'), as opposed to the real BOM table
    header. Distinguished the same way as the BOM check: the real header
    has 'QTY' on the same row nearby; these don't. Plain-English mentions
    of 'ITEM' in note text (e.g. 'ITEM 4 TO REPLACE...') also lack a
    nearby 'SCALE', so they're naturally excluded downstream."""
    item_words = [w for w in words if w[4].strip().upper() == "ITEM"]
    qty_words  = [w for w in words if w[4].strip().upper() == "QTY"]
    detail_items = []
    for iw in item_words:
        iy = (iw[1] + iw[3]) / 2
        has_qty = any(abs((q[1]+q[3])/2 - iy) <= HEADER_ROW_TOLERANCE_PT for q in qty_words)
        if not has_qty:
            detail_items.append(iw)
    return detail_items


def find_item_reference_number(words, item_word):
    """For a detail-view ITEM label, find its ratio line below it (the
    'SCALE 1:20' or bare '1:20' line), then the reference number on that
    same line - identified as the longest all-digit word with
    >= ITEM_REF_MIN_DIGITS digits, which reliably separates it from the
    1-3 digit scale ratio denominator (e.g. the '20' in '1:20'). Anchors
    on the ':' character rather than the word 'SCALE' - some detail views
    show the bare ratio with no 'SCALE' label at all, which a SCALE-word
    anchor would silently miss entirely. Returns None if there's no
    reference-number field at all (some detail views show 'REFER TO
    NOTE X' instead)."""
    item_cy = (item_word[1] + item_word[3]) / 2
    ratio_candidates = [
        w for w in words if w[4].strip() == ":"
        and item_word[0] - ITEM_SCALE_X_MARGIN <= w[0] <= item_word[0] + ITEM_SCALE_X_MARGIN
        and item_cy < (w[1] + w[3]) / 2 <= item_cy + ITEM_SCALE_Y_MARGIN
    ]
    if not ratio_candidates:
        return None, None
    scale = ratio_candidates[0]

    scale_cy = (scale[1] + scale[3]) / 2
    row_words = [
        w for w in words
        if abs((w[1] + w[3]) / 2 - scale_cy) < 2
        # Confirmed on a real drawing: without an X bound here, a
        # dimension value elsewhere on the page (e.g. "1050" on the tank
        # body) that merely happens to share this row's Y-height gets
        # mistaken for this callout's reference number, even when it's
        # nowhere near the actual ITEM/SCALE text.
        and item_word[0] - ITEM_REF_X_MARGIN <= w[0] <= item_word[0] + ITEM_REF_X_MARGIN
    ]
    numeric = [w for w in row_words if w[4].strip().isdigit() and len(w[4].strip()) >= ITEM_REF_MIN_DIGITS]
    if not numeric:
        return scale, None
    ref = max(numeric, key=lambda w: len(w[4].strip()))
    return scale, ref


def run_item_reference_check(page, page_num, report_lines, counts, ensure_page_header):
    words = page.get_text("words")
    detail_items = find_detail_view_items(words)

    for item_word in detail_items:
        scale, ref = find_item_reference_number(words, item_word)
        if scale is None or ref is None:
            continue  # no SCALE nearby, or no reference-number field on this one

        ref_text = ref[4].strip()
        if len(ref_text) == ITEM_REF_EXPECTED_DIGITS:
            report_lines.append(
                f"  Page {page_num + 1}: ITEM at ({item_word[0]:.1f},{item_word[1]:.1f}) "
                f"reference number '{ref_text}' OK"
            )
            continue

        counts["item_reference_length"] += 1
        ensure_page_header()
        print(f"  Page {page_num + 1}: ITEM reference number '{ref_text}' has "
              f"{len(ref_text)} digit(s), expected {ITEM_REF_EXPECTED_DIGITS}")
        report_lines.append(
            f"    [ITEM REFERENCE] '{ref_text}' has {len(ref_text)} digit(s), "
            f"expected {ITEM_REF_EXPECTED_DIGITS}  (ITEM at ({item_word[0]:.1f},{item_word[1]:.1f}))"
        )
        draw_highlight(page, fitz.Rect(ref[0], ref[1], ref[2], ref[3]),
                       label="SIX NO'S?", label_color=HIGHLIGHT_COLOR,
                       label_fontsize=6.72, label_offset_lines=1.0)


# ==================================================================
# CHECK 8: ITEM reference number's last 3 digits must match an
# up-stream-referenced drawing number
# ==================================================================

# How many trailing characters to compare between the ITEM reference
# number and each up-stream drawing number
ITEM_REF_SUFFIX_LEN = 3
# Max vertical distance (points) above the up-stream "DRAWING NUMBER"
# header to still count as a listed reference row
UPSTREAM_ROW_SEARCH_ABOVE_PT = 100.0


def find_upstream_drawing_numbers(words):
    """The 'UP-STREAM REFERENCES' table's list of drawing numbers - found
    via the leftmost 'DRAWING NUMBER' header on the page (there are
    normally two: this one on the far left, and an unrelated one in the
    main title block far to the right - leftmost position reliably picks
    the right one). Values sit ABOVE the header, one per row, each as a
    single hyphenated word (e.g. 'PJ00193-GTA-3450-6-000130')."""
    drawing_headers = []
    for dw in words:
        if dw[4].strip().upper() != "DRAWING":
            continue
        number_match = next(
            (w for w in words if w[4].strip().upper() == "NUMBER"
             and abs(w[1] - dw[1]) < 2 and 0 < w[0] - dw[2] < 10),
            None
        )
        if number_match:
            drawing_headers.append(dw)

    if not drawing_headers:
        return []
    header = min(drawing_headers, key=lambda w: w[0])  # leftmost

    hx0, hx1 = header[0], header[2] + 20  # a little slack for the "NUMBER" word
    header_cy = (header[1] + header[3]) / 2
    rows = [
        w for w in words
        if hx0 - 15 <= w[0] <= hx1 and header_cy - UPSTREAM_ROW_SEARCH_ABOVE_PT <= (w[1]+w[3])/2 < header_cy
        and "-" in w[4]  # a real drawing number always contains hyphens
    ]
    return rows


def run_item_upstream_reference_check(page, page_num, report_lines, counts, ensure_page_header):
    words = page.get_text("words")
    detail_items = find_detail_view_items(words)
    if not detail_items:
        return

    upstream_words = find_upstream_drawing_numbers(words)
    if not upstream_words:
        return  # nothing listed to check against - avoid false positives

    upstream_suffixes = {w[4].strip()[-ITEM_REF_SUFFIX_LEN:]: w for w in upstream_words}
    report_lines.append(
        f"  Page {page_num + 1}: up-stream reference drawing number(s): "
        f"{', '.join(w[4].strip() for w in upstream_words)}"
    )

    for item_word in detail_items:
        scale, ref = find_item_reference_number(words, item_word)
        if scale is None or ref is None:
            continue

        ref_text = ref[4].strip()
        if len(ref_text) < ITEM_REF_SUFFIX_LEN:
            continue
        suffix = ref_text[-ITEM_REF_SUFFIX_LEN:]

        if suffix in upstream_suffixes:
            report_lines.append(
                f"    ITEM reference '{ref_text}' suffix '{suffix}' matches "
                f"up-stream drawing '{upstream_suffixes[suffix][4].strip()}' - OK"
            )
            continue

        counts["item_upstream_mismatch"] += 1
        ensure_page_header()
        print(f"  Page {page_num + 1}: ITEM reference '{ref_text}' (suffix '{suffix}') "
              f"doesn't match any up-stream drawing number")
        report_lines.append(
            f"    [ITEM UPSTREAM] '{ref_text}' (suffix '{suffix}') doesn't match any "
            f"up-stream drawing number  (ITEM at ({item_word[0]:.1f},{item_word[1]:.1f}))"
        )
        draw_highlight(page, fitz.Rect(ref[0], ref[1], ref[2], ref[3]))


# ==================================================================
# CHECK 10: old title-block version (PROJ MANAGER row present)
# ==================================================================

# The current title block ends its signature list at APPROVED - if
# 'PROJ MANAGER' appears as a row label, it's the old template
TITLEBLOCK_LABEL_ROW_TOLERANCE_PT = 3.0
TITLEBLOCK_VERSION_WARNING_TEXT = "UPDATE TITLEBLOCK VERSION"
TITLEBLOCK_WARNING_FONT_SIZE = 4.0


def find_proj_manager_label(words):
    """Find 'PROJ' immediately followed by 'MANAGER' on the same row -
    the old title block's trailing signature-block row label."""
    proj_words    = [w for w in words if w[4].strip().upper() == "PROJ"]
    manager_words = [w for w in words if w[4].strip().upper() == "MANAGER"]
    for pw in proj_words:
        py = (pw[1] + pw[3]) / 2
        for mw in manager_words:
            my = (mw[1] + mw[3]) / 2
            if abs(py - my) <= TITLEBLOCK_LABEL_ROW_TOLERANCE_PT and 0 <= mw[0] - pw[2] <= 20:
                return (pw, mw)
    return None


def run_titleblock_version_check(page, page_num, report_lines, counts, ensure_page_header):
    words = page.get_text("words")
    match = find_proj_manager_label(words)
    if not match:
        return

    pw, mw = match
    counts["titleblock_old_version"] += 1
    ensure_page_header()
    print(f"  Page {page_num + 1}: 'PROJ MANAGER' found - old title block version")
    report_lines.append(
        f"    [TITLEBLOCK VERSION] 'PROJ MANAGER' found at ({pw[0]:.1f},{pw[1]:.1f}) "
        f"- old title block template, current one ends at APPROVED"
    )

    union_rect = fitz.Rect(min(pw[0], mw[0]), min(pw[1], mw[1]), max(pw[2], mw[2]), max(pw[3], mw[3]))
    draw_highlight(page, union_rect, enlarge=False)

    # Place the warning INLINE with the flagged row, immediately to the
    # right of "MANAGER", rather than above it - stamping it above the row
    # collided with "APPROVED" directly above (title-block rows are packed
    # too tightly for that). Staying in the same row and extending
    # rightward (into the usually-blank SIGNED/DATE columns for this row,
    # since PROJ MANAGER is typically the last, unsigned row) avoids
    # colliding with the row above. Small font since the row itself is
    # narrow (~9pt tall).
    try:
        warn_x = mw[2] + 8
        warn_y = max(mw[3] - 1, 0)
        page.insert_text(
            fitz.Point(warn_x, warn_y), TITLEBLOCK_VERSION_WARNING_TEXT,
            fontsize=TITLEBLOCK_WARNING_FONT_SIZE, color=HIGHLIGHT_COLOR,
        )
    except Exception as e:
        report_lines.append(f"    (could not insert warning text label: {e})")


# ==================================================================
# Per-file processing - spelling + N/A + all drawing checks, one pass
# ==================================================================

def detect_problematic_pdf_type(src_path):
    """Detects PDF files that will produce unreliable results with our
    standard text-extraction and geometry checks, and need to be
    re-exported through PyMuPDF's own renderer before checking.

    Two confirmed problematic types:
    1. AutoCAD SHX-font PDFs: visible letters are drawn as vector strokes
       tracing each glyph's shape, so line-crossing detection sees dozens
       of fake 'crossings' per word. Signal: high ratio of drawing items
       to text words on a page, especially when the geometry sanity check
       would fire.
    2. Inventor native-export PDFs: block structure is per-line instead of
       per-paragraph, making the text-overlap block-coincidence check fire
       on adjacent normal lines. Signal: very low average words-per-block
       AND a known Inventor producer string in the PDF metadata.

    Returns: ('shx', page_index) or ('inventor', None) or (None, None)
    """
    try:
        doc = fitz.open(src_path)
        # Check PDF producer metadata for Inventor fingerprint
        metadata = doc.metadata or {}
        producer = (metadata.get('producer') or '').lower()
        creator = (metadata.get('creator') or '').lower()
        is_inventor_meta = 'autodesk' in producer or 'inventor' in producer or \
                           'autodesk' in creator or 'inventor' in creator

        for page_idx, page in enumerate(doc):
            words = page.get_text('words')
            word_count = max(len(words), 1)

            # Inventor fingerprint: metadata PLUS per-line block structure.
            # The SHX/AutoCAD fingerprint (high drawing-items-to-words ratio)
            # was removed after it repeatedly false-triggered on normal busy
            # engineering drawings - the ratio varies too much across real
            # drawings to use as a reliable automatic signal without a
            # confirmed SHX file to calibrate against. Inventor detection
            # uses the more reliable /Producer metadata field instead.
            if is_inventor_meta and len(words) > 20:
                blocks = {}
                for w in words:
                    if len(w) >= 6:
                        blocks.setdefault(w[5], []).append(w)
                if blocks:
                    avg_words_per_block = len(words) / len(blocks)
                    if avg_words_per_block < 2.5:
                        doc.close()
                        return 'inventor', None

        doc.close()
        return None, None
    except Exception:
        return None, None


def normalise_pdf_via_rerender(src_path, out_path, dpi=150):
    """Re-renders each page of src_path as a raster image and writes a
    fresh PDF to out_path. This strips out SHX glyph strokes, Inventor
    block-structure quirks, and other export-specific geometry that
    interferes with our checks - the output contains only rendered pixels
    and embedded image data, which PyMuPDF can still extract text from
    via its internal OCR if needed.

    NOTE: this produces a rasterised PDF. Text extraction from it uses
    OCR (the SpellCheckOCR_Fallback path), not native vector extraction.
    For drawings where spelling accuracy matters more than geometry checks,
    that's acceptable. For geometry-check-only files this works well since
    the checks operate on the visual content, not the vector structure.

    Returns: (out_path, page_count) on success, or (None, error_string).
    """
    try:
        src_doc = fitz.open(src_path)
        out_doc = fitz.open()
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        for page in src_doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
            img_page.insert_image(img_page.rect, pixmap=pix)
        count = len(src_doc)
        src_doc.close()
        out_doc.save(out_path)
        out_doc.close()
        return str(out_path), count
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def strip_existing_annotations(src_path):
    """Makes a temp copy of the PDF with all existing PDF *annotation*
    objects removed (Highlight, Squiggly, StrikeOut, FreeText, Ink, Note,
    Stamp, etc.) - the kind a reviewer adds with a normal PDF comment/
    markup tool - before this tool's own checks ever run against it. This
    stops a checker's own review comment from ever being mistaken for
    something our checks found.

    IMPORTANT LIMITATION, so expectations are set correctly: this only
    removes genuine PDF *annotation* objects, which live separately from
    the page's own drawing content and are exactly what page.annots()
    sees. Reviewer markup that has already been FLATTENED into the page's
    actual content stream (a common side effect of some "export/print to
    PDF" or "flatten markups" steps in tools like Bluebeam) is no longer a
    distinguishable annotation by that point - it's just ordinary page
    content, indistinguishable from real drawing geometry, and no amount
    of annotation-stripping can remove it, because it isn't an annotation
    anymore. That's a different, harder problem - confirmed on a real
    file where a highlighter mark over "SURFACES"/"ACCORDANCE" turned out
    to be exactly this (a filled rectangle baked into page content, zero
    stroke opacity) - see meta_has_visible_stroke(), which handles that
    category separately by requiring a real stroke (not just a fill)
    before counting anything as a line-crossing.

    Returns (temp_path, annotation_count) on success, or (None, error_str)
    if stripping failed for any reason - the caller falls back to
    checking the original file directly rather than losing the check
    entirely over this.
    """
    try:
        doc = fitz.open(str(src_path))
        removed = 0
        for page in doc:
            annots = list(page.annots() or [])
            for annot in annots:
                page.delete_annot(annot)
                removed += 1
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf", prefix="spellcheck_clean_")
        os.close(tmp_fd)
        doc.save(tmp_path)
        doc.close()
        return tmp_path, removed
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def normalize_page_rotation(src_path):
    """RE-ACTIVATED - process_pdf() calls this again. Was paused for a
    while in favor of a coordinate-transform-only approach (rotating word
    positions on read instead of rebuilding the page), but that approach
    was confirmed broken via debug output on a real file - the transform
    rotated content in the wrong direction (a drawing's row-index letters
    ended up spread along the top instead of stacked down the margin).
    This function's own last tested state, before being paused, had
    already reached correct page dimensions and correctly-computed
    landscape geometry - worth resuming and finishing verification on.

    Makes a temp copy of the PDF with rotation issues corrected to
    landscape, and the /Rotate flag reset to 0.

    Tested against a real file and got this wrong twice before landing
    here, so the reasoning is spelled out in full:

    A /Rotate flag on a page can mean two very different things, and
    trusting it blindly is wrong in one of them -
    (1) the raw content (page.cropbox) is ALREADY landscape-shaped, and
        the /Rotate flag is itself the bug - some export/print step
        tagged an already-correct landscape page to display sideways.
        The right fix here is to just clear the flag; the content
        underneath never needed to move.
    (2) the raw content genuinely IS portrait-shaped, and /Rotate is
        CORRECTLY the thing making it display as landscape. Here the
        flag is doing real, necessary work, and it needs to be baked
        into real coordinates (not just cleared, or the content goes
        back to displaying as portrait).

    An earlier version of this always trusted and baked in whatever
    rotation was present, on the theory that would work either way -
    confirmed wrong on a real test file: raw content was already
    landscape (1190.5x841.9), a stray /Rotate 90 was the only problem,
    and faithfully "baking in" that rotation just reproduced the same
    broken portrait result the fix was supposed to remove.

    The distinguishing test used below: would applying this rotation
    take LANDSCAPE raw content and turn it into portrait? If yes, the
    rotation is almost certainly the bug (case 1) and gets cleared
    instead of applied. Otherwise it's trusted and baked in properly
    (case 2). A page with no rotation flag at all is left completely
    untouched either way - that's the "genuinely, deliberately portrait
    title-block" case, which this function should never touch.

    Returns (temp_path, rotated_page_count) on success, or (None,
    error_str) if it failed - caller falls back to the original file
    rather than losing the check over this.
    """
    try:
        src_doc = fitz.open(str(src_path))
        rotated_pages = [p.number for p in src_doc if p.rotation != 0]
        if not rotated_pages:
            src_doc.close()
            return None, 0

        new_doc = fitz.open()
        for page in src_doc:
            rotation = page.rotation  # 0, 90, 180, or 270
            # CropBox (not MediaBox) is the PDF-spec-defined "actually
            # intended to be visible" area - many CAD/plot exporters set
            # MediaBox larger than the real drawing (bleed/padding), with
            # CropBox as the real extent. Using MediaBox here sized the
            # new page too big, leaving real blank space where the true
            # page edge should be - confirmed on a real file (content
            # correctly landscape and unclipped, but not filling the page).
            raw = page.cropbox
            raw_w, raw_h = raw.width, raw.height

            if rotation in (90, 270):
                displayed_w, displayed_h = raw_h, raw_w
            else:
                displayed_w, displayed_h = raw_w, raw_h

            raw_is_landscape = raw_w > raw_h
            would_display_portrait = displayed_h > displayed_w

            if raw_is_landscape and would_display_portrait:
                # The rotation flag would take already-good landscape
                # content and turn it portrait - that's the bug, not a
                # correction. Clear it, don't touch the content.
                target_w, target_h = raw_w, raw_h
                apply_rotate = 0
            else:
                # Rotation appears to be doing real, necessary work
                # (e.g. genuinely portrait raw content being corrected to
                # landscape) - trust it and bake it in.
                target_w, target_h = displayed_w, displayed_h
                apply_rotate = rotation

            new_page = new_doc.new_page(width=target_w, height=target_h)
            # show_pdf_page does NOT automatically apply the source
            # page's own /Rotate value when embedding it - it must be
            # passed explicitly via `rotate=`, or it silently defaults to
            # embedding the raw, unrotated content regardless of what the
            # target box is sized for.
            #
            # Confirmed via a side-by-side comparison against the real
            # original file (rendered correctly, full-bleed, zero margin,
            # in Adobe): our output was leaving a real blank margin the
            # original never had. The new page's SIZE was being computed
            # from CropBox, but `clip` was never passed to show_pdf_page,
            # so it was embedding from whatever ITS OWN default source
            # region is (very possibly a larger MediaBox-based area) and
            # scaling that down to fit our smaller CropBox-sized target -
            # shrinking the real content and leaving exactly this kind of
            # margin. Passing clip=raw makes the embedded region and the
            # target size the same rectangle, so this becomes the
            # lossless 1:1 copy it was always supposed to be.
            new_page.show_pdf_page(new_page.rect, src_doc, page.number, rotate=apply_rotate, clip=raw)
        src_doc.close()

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf", prefix="spellcheck_rot_")
        os.close(tmp_fd)
        new_doc.save(tmp_path)
        new_doc.close()
        return tmp_path, len(rotated_pages)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def process_pdf(pdf_path, all_ignore, spell, report_lines):
    """Thin wrapper around _process_pdf_impl: corrects page rotation if
    needed (see create_rotation_corrected_copy), makes a temp copy of the
    PDF with pre-existing reviewer annotations stripped (see
    strip_existing_annotations), runs the real implementation against
    that copy instead of the original, and guarantees temp files are
    cleaned up afterward regardless of how processing finished (success,
    a flagged file, or an exception) - this is the try/finally a plain
    rename-and-wrap can't skip, since _process_pdf_impl has many early
    return points internally.

    Rotation handling has gone through several approaches - worth being
    explicit about why this one, a pure /Rotate metadata change via
    page.set_rotation(), replaced the others:
    - normalize_page_rotation (still defined, no longer used): physically
      rebuilt pages via show_pdf_page(), which ran into repeated
      clipping/CropBox bugs from picking the wrong source region to embed.
    - RotationAwarePageProxy (still defined, no longer used): kept the
      original file untouched and instead gave checks a transformed VIEW
      of the coordinates via a coordinate matrix - direction confirmed
      wrong twice.
    - ocr_extract_words_via_rotated_image (removed entirely - see
      _try_ocr_rotated_image's docstring for the full account): rendered
      the page then manually rotated the SAVED IMAGE again with Pillow.
      Confirmed on a real drawing to be a genuine double-rotation bug -
      page.get_pixmap() already applies the page's own /Rotate flag
      automatically, so the image was already correct before the manual
      rotation ran. The BOM/REV/title-block OCR path (see the main
      per-page loop) now reuses the standard ocr_fallback.ocr_extract_words()
      + OCRPageProxy pipeline directly, with no rotation handling of its
      own needed at all.
    A plain metadata flag change avoids all of that: the real page
    content and coordinate space are never touched, so once the flag
    matches how the page should actually display, get_text()/
    get_drawings()/draw_rect() all read and write consistently using the
    REAL extracted text - no OCR, no separate readable/native coordinate
    bookkeeping needed at all. The corrected copy is placed directly in
    the SPELLCHECK DWGS output folder (not a hidden temp file) so it's
    visible for confirming the correction, and the final output filename
    is unaffected either way, since out_path naming is always derived
    from the ORIGINAL pdf_path, never from working_path."""
    temp_paths = []
    working_path = str(pdf_path)

    # Automatic /Rotate correction, now using find_best_rotation_via_ocr /
    # create_rotation_corrected_copy_via_ocr - render + OCR based, not
    # text-extraction based. The original approach (find_best_rotation_setting,
    # now dead code, kept documented) was confirmed broken with direct
    # diagnostic evidence: page.set_rotation(candidate) followed
    # immediately by get_text("words") returned the IDENTICAL word list
    # and coordinates for every one of the four candidate values (0/90/
    # 180/270) on two real files - get_text() reads the underlying
    # content stream, which /Rotate (a pure display-time transform) never
    # touches, so that approach could never actually distinguish a
    # correct rotation from an incorrect one. Rendering DOES correctly
    # vary with /Rotate - independently confirmed by the existing,
    # working zero-extractable-text OCR fallback pipeline, which relies
    # on the exact same page.get_pixmap() behavior - so trying each
    # candidate, rendering it, and OCR'ing that render can actually tell
    # them apart.
    #
    # A non-zero /Rotate flag is still not, on its own, evidence that
    # anything is wrong - the MIN_ROTATION_CONFIDENCE_SCORE guard means a
    # file with no real signal either way is left completely untouched,
    # same principle as before, just with a detection method that
    # actually works.
    try:
        probe_doc = fitz.open(working_path)
        needs_rotation_fix = any(p.rotation != 0 for p in probe_doc)
        probe_doc.close()
    except Exception:
        needs_rotation_fix = False

    if needs_rotation_fix and ocr_fallback is not None:
        tesseract_exe = ocr_fallback.find_tesseract_exe()
        if tesseract_exe:
            out_folder = Path(pdf_path).resolve().parent / "SPELLCHECK DWGS"
            out_folder.mkdir(exist_ok=True)
            rotated_copy_path = out_folder / (Path(pdf_path).stem + "_ROTATED.pdf")
            winning_rotation, score_or_err = create_rotation_corrected_copy_via_ocr(
                working_path, rotated_copy_path, tesseract_exe, debug_log=report_lines
            )
            if winning_rotation is not None:
                working_path = str(rotated_copy_path)
                temp_paths.append(str(rotated_copy_path))
                report_lines.append(
                    f"  Page rotation detected - created a corrected copy "
                    f"({rotated_copy_path.name}) with /Rotate set to {winning_rotation}deg "
                    f"(auto-picked via render+OCR, based on {score_or_err} title-block "
                    f"keyword match(es) found at the best candidate) and checked that "
                    f"instead. This intermediate copy is deleted once the _SpellCheck.pdf "
                    f"output has been produced from it."
                )
            else:
                report_lines.append(
                    f"  NOTE: this file's /Rotate flag is non-zero, but no rotation "
                    f"correction was applied ({score_or_err}). A non-zero /Rotate flag "
                    f"is normal, valid PDF structure by itself and is not evidence of a "
                    f"problem - checking the file with its own rotation exactly as-is."
                )
        else:
            report_lines.append(
                f"  NOTE: this file's /Rotate flag is non-zero, but no Tesseract-OCR "
                f"install was found, so no rotation correction could be attempted - "
                f"checking the file with its own rotation exactly as-is."
            )
    elif needs_rotation_fix:
        report_lines.append(
            f"  NOTE: this file's /Rotate flag is non-zero, but the OCR fallback "
            f"module isn't available, so no rotation correction could be attempted - "
            f"checking the file with its own rotation exactly as-is."
        )

    # Detect and normalise problematic PDF types (SHX-font AutoCAD, Inventor
    # native export) by re-rendering to a fresh PDF before checking. This
    # uses the same temp-copy pattern as the rotation fix above: working_path
    # is replaced, the temp is tracked in temp_paths for cleanup, and the
    # final _SpellCheck.pdf output name is always derived from the original
    # pdf_path so nothing visible to the user changes.
    pdf_type, type_detail = detect_problematic_pdf_type(working_path)
    if pdf_type in ('shx', 'inventor'):
        type_label = 'AutoCAD SHX-font' if pdf_type == 'shx' else 'Inventor native-export'
        out_folder = Path(pdf_path).resolve().parent / "SPELLCHECK DWGS"
        out_folder.mkdir(exist_ok=True)
        normalised_path = out_folder / (Path(pdf_path).stem + "_NORMALISED.pdf")
        result_path, detail = normalise_pdf_via_rerender(working_path, str(normalised_path))
        if result_path:
            working_path = result_path
            temp_paths.append(result_path)
            report_lines.append(
                f"  {type_label} PDF detected - re-rendered to a normalised copy "
                f"({normalised_path.name}) to avoid false positives from export-specific "
                f"geometry (SHX glyph strokes / Inventor per-line block structure). "
                f"Checks run on the normalised copy; this intermediate file is deleted "
                f"once the _SpellCheck.pdf output has been produced."
            )
        else:
            report_lines.append(
                f"  NOTE: {type_label} PDF detected but normalisation failed "
                f"({detail}) - checking the original file as-is, which may produce "
                f"false positives on geometry and text-overlap checks."
            )

    stripped_path, strip_result = strip_existing_annotations(working_path)
    if stripped_path:
        working_path = stripped_path
        temp_paths.append(stripped_path)
        if strip_result:
            report_lines.append(
                f"  Removed {strip_result} pre-existing PDF annotation(s) from a temp "
                f"working copy before checking (existing reviewer markup, not this "
                f"tool's own highlights)."
            )
    else:
        report_lines.append(
            f"  NOTE: could not create an annotation-stripped temp copy "
            f"({strip_result}) - checking the original file directly instead."
        )

    try:
        return _process_pdf_impl(pdf_path, working_path, all_ignore, spell, report_lines)
    finally:
        for p in temp_paths:
            try:
                os.remove(p)
            except OSError:
                pass


def _process_pdf_impl(pdf_path, working_path, all_ignore, spell, report_lines):
    src        = Path(pdf_path).resolve()
    out_folder = src.parent / "SPELLCHECK DWGS"
    out_folder.mkdir(exist_ok=True)
    out_path   = out_folder / (src.stem + "_SpellCheck.pdf")

    print(f"\n  Source : {src.name}")
    print(f"  Output : {out_path.name}")

    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append(f"FILE: {src.name}")
    report_lines.append("=" * 60)

    try:
        doc = fitz.open(str(working_path))
    except Exception as e:
        msg = f"Failed to open PDF:\n{e}"
        print("  ERROR: " + msg)
        show_message("Error", msg, error=True)
        return None

    reference_project_number = get_reference_project_number(pdf_path)
    # Full filename stem (no extension) used for the drawing-number-vs-filename check.
    reference_drawing_stem = Path(pdf_path).stem

    total_misspelled = 0
    total_na = 0
    total_words_seen = 0
    ocr_pages_used = 0
    counts = {
        "line": 0, "text_overlap": 0, "balloon_overlap": 0, "magenta_dimension": 0,
        "bom_out_of_seq": 0, "bom_missing": 0, "bom_no_balloon": 0, "project_number": 0,
        "rev_stamp_wrong": 0, "rev_stamp_missing": 0, "rev_stamp_conflict": 0,
        "rev_compare_mismatch": 0, "rev_description_mismatch": 0,
        "item_reference_length": 0, "item_upstream_mismatch": 0,
        "titleblock_old_version": 0,
    }

    for page_num in range(len(doc)):
        page = OnPageWordsProxy(doc[page_num])
        # Layout-sensitive checks (BOM table, REV corner box, project
        # number, revision description, title-block version) all assume
        # a standard landscape layout - "same row", "bottom-right
        # corner", etc. The file itself always stays in its original
        # orientation (no page reconstruction - see process_pdf).
        #
        # For a rotated page, these checks go through OCR instead of
        # trying to correct get_text("words") coordinates directly - two
        # separate attempts at that (using PyMuPDF's rotation_matrix /
        # derotation_matrix) each produced a different, confirmed-wrong
        # result on a real file, and there's no way to run PyMuPDF here
        # to verify the correct direction. Rendering the page to an image
        # and running OCR sidesteps that problem entirely: page.get_pixmap()
        # is a fundamental, heavily-used rendering operation that reliably
        # produces a visually-correct image regardless of /Rotate.
        #
        # This now calls the exact same ocr_fallback.ocr_extract_words()
        # + OCRPageProxy pipeline already used for zero-extractable-text
        # pages, with NO extra rotation handling of our own. A prior
        # version manually rotated the ALREADY-correctly-rendered image a
        # second time with Pillow (see the dead _try_ocr_rotated_image
        # for the full account) - confirmed on a real drawing to
        # incorrectly rotate a page that was already displaying
        # correctly. render_page_to_image()'s plain page.get_pixmap(
        # matrix=...) call already applies the page's own /Rotate flag
        # automatically, and does so consistently with every other
        # PyMuPDF coordinate operation on the same page - so no separate
        # rotation-direction guess, trial, or coordinate-space mapping is
        # needed at all.
        structural_page = page
        if page.rotation and ocr_fallback is not None:
            tesseract_exe = ocr_fallback.find_tesseract_exe()
            if tesseract_exe:
                ocr_words, ocr_diag = ocr_fallback.ocr_extract_words(page, tesseract_exe)
                if ocr_words:
                    structural_page = ocr_fallback.OCRPageProxy(page, ocr_words)
                    report_lines.append(
                        f"  Page {page_num + 1} is rotated - used OCR on the page's "
                        f"already-correctly-rendered image ({len(ocr_words)} word(s) read) "
                        f"for the BOM/REV/project-number/title-block checks specifically "
                        f"(spelling and line-crossing/overlap keep using the real "
                        f"extracted text, unaffected by rotation). OCR is less accurate "
                        f"than direct text extraction - worth a manual check of those "
                        f"specific results on this file."
                    )
                else:
                    report_lines.append(
                        f"  Page {page_num + 1} is rotated - OCR produced no usable text "
                        f"({ocr_diag}), so BOM/REV/project-number/title-block checks are "
                        f"running on raw (likely misaligned) coordinates and may not "
                        f"reliably locate things on this file."
                    )
            else:
                report_lines.append(
                    f"  Page {page_num + 1} is rotated and no Tesseract-OCR install was "
                    f"found, so BOM/REV/project-number/title-block checks are running on "
                    f"raw (likely misaligned) coordinates and may not reliably locate "
                    f"things on this file."
                )
        elif page.rotation:
            report_lines.append(
                f"  Page {page_num + 1} is rotated and the OCR fallback module isn't "
                f"available, so BOM/REV/project-number/title-block checks are running on "
                f"raw (likely misaligned) coordinates and may not reliably locate things "
                f"on this file."
            )
        print(f"    Page {page_num + 1}/{len(doc)} ...", end=" ", flush=True)

        mupdf_words = page.get_text("words")
        # mupdf_words: (x0, y0, x1, y1, word, block_no, line_no, word_no)
        total_words_seen += len(mupdf_words)

        page_reported = False

        def ensure_page_header():
            nonlocal page_reported
            if not page_reported:
                report_lines.append(f"  Page {page_num + 1}:")
                page_reported = True

        # --- OCR fallback for a page with zero extractable text ---
        # Only the structural checks (BOM/REV/project-number/title-block)
        # run on OCR'd text - spelling, N/A search, and the geometry checks
        # all need either real text objects or real vector geometry
        # alignment that OCR can't reliably provide, so this page's
        # coverage is intentionally narrower than a normal page's.
        if not mupdf_words and ocr_fallback is None and _ocr_import_error:
            report_lines.append(
                f"  Page {page_num + 1}: OCR fallback module failed to load "
                f"({_ocr_import_error}) - OCR was never attempted for this page."
            )
        if not mupdf_words and ocr_fallback is not None:
            tesseract_exe = ocr_fallback.find_tesseract_exe()
            if tesseract_exe:
                used_ocr, ocr_diagnostic = ocr_fallback.run_ocr_fallback_checks(
                    sys.modules[__name__], page, page_num, reference_project_number,
                    report_lines, counts, ensure_page_header, tesseract_exe,
                )
                if used_ocr:
                    ocr_pages_used += 1
                    print(f"used OCR fallback")
                    continue
                elif ocr_diagnostic:
                    report_lines.append(f"  Page {page_num + 1}: OCR fallback produced no usable text - {ocr_diagnostic}")

        # --- N/A mass reference check (independent of spellcheck logic) ---
        na_rects = page.search_for("N/A")
        if na_rects:
            total_na += len(na_rects)
            print(f"found {len(na_rects)} 'N/A' instance(s)  ", end="")
            report_lines.append(f"  Page {page_num + 1}: {len(na_rects)} 'N/A' mass reference instance(s) found")
            for rect in na_rects:
                pad_h = (rect.x1 - rect.x0) / 2
                pad_v = (rect.y1 - rect.y0) / 2
                draw_rect = fitz.Rect(
                    rect.x0 - pad_h, rect.y0 - pad_v,
                    rect.x1 + pad_h, rect.y1 + pad_v,
                )
                shape = page.new_shape()
                shape.draw_rect(draw_rect)
                shape.finish(
                    fill=NA_HIGHLIGHT_COLOR, color=NA_HIGHLIGHT_COLOR,
                    fill_opacity=NA_HIGHLIGHT_ALPHA, stroke_opacity=0,
                )
                shape.commit()

        # --- Spelling check ---
        if not mupdf_words:
            print("no text found")
            report_lines.append(f"  Page {page_num + 1}: No text found")
        else:
            token_list = []
            for w in mupdf_words:
                raw     = w[4].strip()
                cleaned = clean_token(raw)
                if not cleaned:
                    continue
                token_list.append({
                    "raw":     raw,
                    "cleaned": cleaned,
                    "lower":   cleaned.lower(),
                    "x0": w[0], "y0": w[1],
                    "x1": w[2], "y1": w[3],
                    "line_y":  round(w[1]),
                })

            candidates = {}
            for i, tok in enumerate(token_list):
                if not is_candidate(tok["cleaned"], all_ignore):
                    continue
                if i + 1 < len(token_list):
                    next_raw = token_list[i + 1]["raw"].strip()
                    if next_raw and next_raw[0].isdigit():
                        continue
                raw = tok["raw"].strip()
                if re.search(r'[A-Za-z]\d', raw):
                    continue
                candidates[tok["lower"]] = tok

            if not candidates:
                print(f"OK (0 candidates from {len(token_list)} tokens)")
            else:
                bad_tokens = spell.unknown(candidates.keys())
                print(f"({len(candidates)} candidates, {len(bad_tokens)} flagged)", end="  ")
                confirmed_bad = set()
                all_tokens_raw = [re.sub(r"[^A-Za-z]", "", t["raw"]).upper() for t in token_list]
                line_y_list    = [t["line_y"] for t in token_list]

                for bad in bad_tokens:
                    if bad in all_ignore:
                        continue
                    if len(bad) > 10 and split_into_valid_words(bad, spell):
                        continue

                    is_fragment = False
                    if len(bad) <= 10:
                        for idx, tok in enumerate(token_list):
                            if tok["lower"] != bad:
                                continue
                            curr_y = line_y_list[idx]

                            for look_back in range(1, 3):
                                if idx - look_back < 0:
                                    break
                                if abs(line_y_list[idx - look_back] - curr_y) > 8:
                                    break
                                prev = "".join(
                                    all_tokens_raw[idx - b]
                                    for b in range(look_back, 0, -1)
                                    if abs(line_y_list[idx - b] - curr_y) <= 8
                                )
                                for take in range(1, min(len(prev) + 1, 8)):
                                    combo = (prev[-take:] + bad).lower()
                                    if len(combo) >= 5 and combo in spell:
                                        is_fragment = True
                                        break
                                if is_fragment:
                                    break

                            if not is_fragment:
                                for look_fwd in range(1, 3):
                                    if idx + look_fwd >= len(token_list):
                                        break
                                    if abs(line_y_list[idx + look_fwd] - curr_y) > 8:
                                        break
                                    nxt = "".join(
                                        all_tokens_raw[idx + f]
                                        for f in range(1, look_fwd + 1)
                                        if abs(line_y_list[idx + f] - curr_y) <= 8
                                    )
                                    for take in range(1, min(len(nxt) + 1, 8)):
                                        combo = (bad + nxt[:take]).lower()
                                        if len(combo) >= 5 and combo in spell:
                                            is_fragment = True
                                            break
                                    if is_fragment:
                                        break

                            if is_fragment:
                                break

                    if not is_fragment:
                        confirmed_bad.add(bad)

                confirmed_bad = {b for b in confirmed_bad if b not in all_ignore}

                if confirmed_bad:
                    print(f"{len(confirmed_bad)} issue(s):")
                    ensure_page_header()
                    report_lines.append(f"    {len(confirmed_bad)} spelling issue(s)")
                    for bad in sorted(confirmed_bad):
                        suggestion = spell.correction(bad)
                        print(f"      '{bad}'  ->  did you mean '{suggestion}'?")
                        report_lines.append(
                            f"    - '{bad.upper()}'  ->  suggestion: '{suggestion.upper() if suggestion else '?'}'"
                        )
                    for tok in token_list:
                        if tok["lower"] in confirmed_bad:
                            w = tok["x1"] - tok["x0"]
                            h = tok["y1"] - tok["y0"]
                            pad_h = 2.0
                            pad_v = h * 0.1
                            draw_rect = fitz.Rect(
                                tok["x0"] - pad_h, tok["y0"] - pad_v,
                                tok["x1"] + pad_h, tok["y1"] + pad_v,
                            )
                            shape = page.new_shape()
                            shape.draw_rect(draw_rect)
                            shape.finish(
                                fill=(1, 0.2, 0.2), color=(1, 0.2, 0.2),
                                fill_opacity=0.45, stroke_opacity=0,
                            )
                            shape.commit()
                    total_misspelled += len(confirmed_bad)
                else:
                    print("OK")

        # --- Drawing-consistency checks ---
        # Pass mupdf_words so run_geometry_checks doesn't call get_text("words") again.
        detected_balloons = run_geometry_checks(page, page_num, report_lines, counts, ensure_page_header, words=mupdf_words)
        run_bom_sequence_check(structural_page, page_num, report_lines, counts, ensure_page_header, balloons=detected_balloons)
        run_project_number_check(structural_page, page_num, reference_project_number, report_lines, counts, ensure_page_header, words=mupdf_words)
        run_drawing_number_check(structural_page, page_num, reference_drawing_stem, report_lines, counts, ensure_page_header, words=mupdf_words)
        run_revision_stamp_check(structural_page, page_num, report_lines, counts, ensure_page_header)
        run_rev_compare_check(structural_page, page_num, report_lines, counts, ensure_page_header)
        run_rev_description_check(structural_page, page_num, report_lines, counts, ensure_page_header)
        run_item_reference_check(page, page_num, report_lines, counts, ensure_page_header)
        run_item_upstream_reference_check(page, page_num, report_lines, counts, ensure_page_header)
        run_titleblock_version_check(structural_page, page_num, report_lines, counts, ensure_page_header)

    total_drawing_flags = sum(counts.values())
    total_issues = total_misspelled + total_na + total_drawing_flags

    if total_words_seen == 0 and ocr_pages_used == 0:
        # No text objects anywhere on this PDF at all, and OCR either
        # wasn't available or couldn't read anything either - every check
        # above silently found nothing to examine because there was
        # genuinely nothing readable, not because the drawing is clean.
        # Confirmed cause on a real file: exported from AutoCAD via a
        # pdfplot driver with zero /Font resources in the page - text was
        # flattened to vector outline geometry (typical of SHX-font
        # AutoCAD drawings), which no text-extraction tool (this one or
        # otherwise) can read directly. Flag this distinctly so it never
        # looks identical to a genuine "checked and found nothing wrong"
        # result.
        print("  *** NO EXTRACTABLE TEXT FOUND - every check was skipped, this is NOT a 'clean' result ***")
        print("      (likely a vector-outlined/SHX-font export - text-based checking cannot read this file)")
        report_lines.append("  RESULT: SKIPPED - No extractable text found on any page")
        if ocr_fallback is None:
            report_lines.append(
                "  *** WARNING: this file could not be checked at all (0 text objects found) - "
                "likely exported with text flattened to vector outlines (common with AutoCAD SHX "
                "fonts). The OCR fallback module itself never loaded, so it was never attempted: "
                f"{_ocr_import_error or 'unknown import error'}. Make sure SpellCheckOCR_Fallback.py "
                "is in the same folder as this script. This is NOT the same as a clean/passed "
                "result. ***"
            )
        elif ocr_fallback.find_tesseract_exe() is None:
            report_lines.append(
                "  *** WARNING: this file could not be checked at all (0 text objects found) - "
                "likely exported with text flattened to vector outlines (common with AutoCAD SHX "
                "fonts). An OCR fallback exists but no Tesseract-OCR install was found. Checked:\n"
                f"{ocr_fallback.describe_tesseract_search()}\n"
                "  If Tesseract is installed somewhere else, put its full path (to tesseract.exe) "
                "as a single line in TesseractPath.txt next to this script. This is NOT the same "
                "as a clean/passed result. ***"
            )
        else:
            report_lines.append(
                "  *** WARNING: this file could not be checked at all (0 text objects found, and "
                "the OCR fallback found no readable text either). Likely exported with text "
                "flattened to vector outlines (common with AutoCAD SHX fonts). This is NOT the "
                "same as a clean/passed result. ***"
            )
        doc.close()
        zero_counts = dict(counts)
        return out_path, 0, 0, zero_counts, True, False

    ocr_used = ocr_pages_used > 0
    if ocr_used:
        report_lines.append(
            f"  NOTE: {ocr_pages_used} page(s) had no extractable text and used the OCR "
            f"fallback instead - only BOM/REV/project-number/title-block checks ran on those "
            f"page(s); spelling and line-crossing/overlap checks were skipped for them."
        )

    if total_issues == 0:
        print("  No issues found - skipping _SpellCheck output.")
        report_lines.append("  RESULT: PASSED - No issues found")
        doc.close()
        zero_counts = dict(counts)
        return out_path, 0, 0, zero_counts, False, ocr_used

    try:
        doc.save(str(out_path))
        doc.close()
    except Exception as e:
        msg = f"Failed to save output PDF:\n{e}"
        print("  ERROR: " + msg)
        show_message("Error", msg, error=True)
        return None

    print(f"  Done!  {total_misspelled} spelling, {total_na} N/A, "
          f"{total_drawing_flags} drawing-check issue(s) -> {out_path.name}")
    report_lines.append(
        f"  RESULT: FAILED - {total_misspelled} spelling issue(s), "
        f"{total_na} 'N/A' mass reference instance(s), "
        f"{total_drawing_flags} drawing-check issue(s)"
    )
    if total_na > 0:
        report_lines.append("  *** MASS NEEDS UPDATING - 'N/A' found in mass reference ***")
    if counts["rev_stamp_wrong"] or counts["rev_stamp_missing"] or counts["rev_stamp_conflict"]:
        report_lines.append("  *** REVISION STAMP ISSUE - check PRELIMINARY/APPROVED stamp vs REV ***")
    if counts["rev_compare_mismatch"] or counts["rev_description_mismatch"]:
        report_lines.append("  *** REV MISMATCH - corner REV doesn't agree with revisions table ***")
    report_lines.append(f"  OUTPUT: {out_path.name}")
    return out_path, total_misspelled, total_na, counts, False, ocr_used
def clean_spellcheck_folders(pdf_paths):
    """
    Remove any existing SPELLCHECK DWGS output (old *_SpellCheck.pdf files and
    the report) before this run, so re-running after fixing spelling mistakes
    or updating the ignore list doesn't leave stale highlighted PDFs behind.
    Handles all unique parent folders among the selected PDFs.
    """
    seen_folders = set()
    for pdf_path in pdf_paths:
        folder = Path(pdf_path).resolve().parent / "SPELLCHECK DWGS"
        if folder in seen_folders:
            continue
        seen_folders.add(folder)
        if folder.exists():
            try:
                shutil.rmtree(folder)
                print(f"  Cleared old output folder: {folder}")
            except Exception as e:
                # Most likely cause: a _SpellCheck.pdf is still open in a
                # viewer and the OS has it locked - warn but keep going,
                # the new file will just fail to overwrite that one PDF
                print(f"  Warning: could not fully clear {folder}: {e}")
                show_message(
                    "Warning",
                    f"Could not fully clear old output folder:\n{folder}\n\n"
                    f"{e}\n\nThis usually means a _SpellCheck.pdf is still open "
                    f"in a PDF viewer. Close it and re-run if needed.",
                    error=True,
                )


DRAWING_COUNT_KEYS = [
    "line", "text_overlap", "balloon_overlap", "magenta_dimension",
    "bom_out_of_seq", "bom_missing", "bom_no_balloon", "project_number",
    "rev_stamp_wrong", "rev_stamp_missing", "rev_stamp_conflict",
    "rev_compare_mismatch", "rev_description_mismatch",
    "item_reference_length", "item_upstream_mismatch",
    "titleblock_old_version",
]


def main():
    extra_ignore = load_ignore_words()
    all_ignore   = CUSTOM_IGNORE | extra_ignore

    # Create spell checker - deliberately NOT loading ignore words into it
    # Loading words into the frequency model corrupts the dictionary
    # causing correctly spelled words to be flagged as unknown
    spell = SpellChecker()

    pdf_paths = pick_pdfs()
    if not pdf_paths:
        print("No file(s) selected - exiting.")
        return

    print(f"\n{len(pdf_paths)} file(s) selected.")

    # Remove any leftover output from a previous run before processing,
    # so fixed drawings don't leave stale highlighted PDFs behind
    clean_spellcheck_folders(pdf_paths)

    from datetime import datetime
    report_lines = [
        "SPELL CHECK + DRAWING CHECK REPORT",
        f"Generated  : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Files      : {len(pdf_paths)} selected",
        f"Build      : {BUILD_MARKER}",
        "",
    ]

    results      = []
    failed       = []
    no_text_files = []
    total_errors = 0
    total_na_all = 0
    drawing_totals = {k: 0 for k in DRAWING_COUNT_KEYS}
    ocr_used_files = []

    for idx, pdf_path in enumerate(pdf_paths, start=1):
        print(f"\n{'='*60}")
        print(f"Processing {idx}/{len(pdf_paths)}: {Path(pdf_path).name}")
        print(f"{'='*60}")
        try:
            result = process_pdf(pdf_path, all_ignore, spell, report_lines)
            if result:
                out_path, mis_count, na_count, counts, no_text, ocr_used = result
                if no_text:
                    # 0 extractable text objects anywhere on the page - every
                    # check was skipped, this is NOT a clean/passed result,
                    # so it's tracked completely separately and never mixed
                    # into the normal clean/issues categories below
                    no_text_files.append(out_path)
                    continue
                if ocr_used:
                    # Some page(s) had no direct text and used the OCR
                    # fallback instead - tracked separately so it's clear
                    # this file got reduced check coverage, without
                    # excluding it from the normal results entirely
                    ocr_used_files.append(out_path)
                drawing_count = sum(counts.values())
                total_count = mis_count + na_count + drawing_count
                results.append((out_path, mis_count, na_count, counts))
                total_errors += total_count
                total_na_all += na_count
                for k in DRAWING_COUNT_KEYS:
                    drawing_totals[k] += counts[k]
            else:
                failed.append(pdf_path)
        except Exception:
            tb = traceback.format_exc()
            print("UNHANDLED ERROR:\n" + tb)
            show_message("Error", f"Error processing {Path(pdf_path).name}:\n\n{tb}", error=True)
            failed.append(pdf_path)

    # Summary
    def total_of(counts_or_tuple):
        _, m, n, c = counts_or_tuple
        return m + n + sum(c.values())

    with_errors     = [r for r in results if total_of(r) > 0]
    spelling_issues = [r for r in results if r[1] > 0]
    mass_issues     = [r for r in results if r[2] > 0]
    drawing_issues  = [r for r in results if sum(r[3].values()) > 0]
    clean           = [r for r in results if total_of(r) == 0]

    total_drawing_all = sum(drawing_totals.values())

    # Write report file
    try:
        first_folder = Path(pdf_paths[0]).parent / "SPELLCHECK DWGS"
        first_folder.mkdir(exist_ok=True)
        report_path  = first_folder / "SpellCheckReport.txt"
        report_lines += [
            "",
            "=" * 60,
            "SUMMARY",
            "=" * 60,
            f"Total files processed : {len(results)}/{len(pdf_paths)}",
            f"Total issues found    : {total_errors}",
            f"Total 'N/A' mass reference instance(s) : {total_na_all}",
            f"Total drawing-check issue(s) : {total_drawing_all}",
            f"Files passed (clean)  : {len(clean)}",
            f"Files with spelling issues : {len(spelling_issues)}",
            f"Files with MASS NEEDS UPDATING : {len(mass_issues)}",
            f"Files with drawing-check issues : {len(drawing_issues)}",
            f"Files with NO EXTRACTABLE TEXT (SKIPPED - not checked) : {len(no_text_files)}",
            f"Files using OCR fallback (reduced check coverage) : {len(ocr_used_files)}",
            "",
            "Drawing-check breakdown:",
            f"  Line crossings            : {drawing_totals['line']}",
            f"  Text-on-text overlap      : {drawing_totals['text_overlap']}",
            f"  Balloon-on-balloon        : {drawing_totals['balloon_overlap']}",
            f"  Magenta/dangling dims     : {drawing_totals['magenta_dimension']}",
            f"  BOM out of sequence       : {drawing_totals['bom_out_of_seq']}",
            f"  BOM missing numbers       : {drawing_totals['bom_missing']}",
            f"  BOM item no balloon       : {drawing_totals['bom_no_balloon']}",
            f"  Project number mismatch   : {drawing_totals['project_number']}",
            f"  Rev stamp wrong           : {drawing_totals['rev_stamp_wrong']}",
            f"  Rev stamp missing         : {drawing_totals['rev_stamp_missing']}",
            f"  Rev stamp conflict        : {drawing_totals['rev_stamp_conflict']}",
            f"  Rev corner/table mismatch : {drawing_totals['rev_compare_mismatch']}",
            f"  Rev description mismatch  : {drawing_totals['rev_description_mismatch']}",
            f"  Item reference wrong length : {drawing_totals['item_reference_length']}",
            f"  Item upstream ref mismatch  : {drawing_totals['item_upstream_mismatch']}",
            f"  Old title block version     : {drawing_totals['titleblock_old_version']}",
        ]
        with open(str(report_path), "w", encoding="utf-8") as rf:
            rf.write("\n".join(report_lines))
        print(f"\nReport saved to: {report_path}")
    except Exception as e:
        print(f"  Warning: could not write report: {e}")

    summary  = "Spell-check + drawing-check complete!\n\n"
    summary += f"Files processed : {len(results)}/{len(pdf_paths)}\n"
    summary += f"Total highlights: {total_errors}\n"
    if total_na_all > 0:
        summary += f"\n*** MASS NEEDS UPDATING *** - 'N/A' found in {total_na_all} mass reference instance(s)\n"
    if drawing_totals['rev_stamp_wrong'] or drawing_totals['rev_stamp_missing'] or drawing_totals['rev_stamp_conflict']:
        summary += "\n*** REVISION STAMP ISSUE *** - check PRELIMINARY/APPROVED stamp vs REV\n"
    if drawing_totals['rev_compare_mismatch'] or drawing_totals['rev_description_mismatch']:
        summary += "\n*** REV MISMATCH *** - corner REV doesn't agree with revisions table\n"
    if drawing_totals['titleblock_old_version']:
        summary += "\n*** OLD TITLE BLOCK VERSION *** - 'PROJ MANAGER' row found, update the template\n"
    if no_text_files:
        summary += (
            f"\n*** WARNING: {len(no_text_files)} file(s) had NO EXTRACTABLE TEXT and were "
            f"NOT CHECKED AT ALL *** - this is not the same as clean/passed. Likely exported "
            f"with text flattened to vector outlines (common with AutoCAD SHX fonts).\n"
        )
    if ocr_used_files:
        summary += (
            f"\n*** {len(ocr_used_files)} file(s) had no extractable text and used the OCR "
            f"fallback instead *** - only BOM/REV/project-number/title-block checks ran on "
            f"those pages; spelling and line-crossing/overlap checks were skipped for them.\n"
        )

    if mass_issues:
        summary += "\nFiles with MASS NEEDS UPDATING ('N/A' mass reference):\n"
        for out_path, mis_count, na_count, counts in mass_issues:
            summary += f"  {out_path.name}  ({na_count} instance(s))\n"
    if spelling_issues:
        summary += "\nFiles with spelling issues:\n"
        for out_path, mis_count, na_count, counts in spelling_issues:
            summary += f"  {out_path.name}  ({mis_count} spelling issue(s))\n"
    if drawing_issues:
        summary += "\nFiles with drawing-check issues (in SPELLCHECK DWGS folder):\n"
        for out_path, mis_count, na_count, counts in drawing_issues:
            dtotal = sum(counts.values())
            summary += f"  {out_path.name}  ({dtotal} drawing-check issue(s))\n"
    if clean:
        summary += "\nFiles with no issues:\n"
        for out_path, _, _, _ in clean:
            summary += f"  {out_path.stem.replace('_SpellCheck', '')}  (clean)\n"
    if no_text_files:
        summary += "\nFiles SKIPPED - no extractable text (NOT checked):\n"
        for out_path in no_text_files:
            summary += f"  {Path(out_path).stem.replace('_SpellCheck', '')}\n"
    if ocr_used_files:
        summary += "\nFiles using OCR fallback (reduced check coverage):\n"
        for out_path in ocr_used_files:
            summary += f"  {Path(out_path).stem.replace('_SpellCheck', '')}\n"
    if failed:
        summary += "\nFailed:\n"
        for f in failed:
            summary += f"  {Path(f).name}\n"
    summary += "\nReport: SPELLCHECK DWGS\\SpellCheckReport.txt"

    print("\n" + summary)
    show_message("Spell-Check Complete", summary)

    # Open each flagged PDF
    for out_path, mis_count, na_count, counts in with_errors:
        if out_path.exists():
            os.startfile(str(out_path))

    # Open the SPELLCHECK DWGS folder in Windows Explorer
    if pdf_paths:
        spell_check_folder = Path(pdf_paths[0]).parent / "SPELLCHECK DWGS"
        if spell_check_folder.exists():
            os.startfile(str(spell_check_folder))


if __name__ == "__main__":
    main()
