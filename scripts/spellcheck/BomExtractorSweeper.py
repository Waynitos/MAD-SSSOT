"""
BOM EXTRACTOR - PDF - ACAD - INVENTOR - CLEAN SWEEPER
======================================================
Combined BOM extractor — select PDF, AutoCAD DWG, or Inventor IDW/DWG drawings,
extract the Bill of Materials from each, and write everything to a single Excel
workbook ready for distribution.

  PDF   → PyMuPDF text extraction; Tesseract OCR fallback for SHX/rasterised PDFs
            SHX PDFs are omitted from output; a second picker opens for their native DWGs
  DWG   → AutoCAD COM automation (reads block attributes directly — no OCR)
            Used as a supplement when SHX PDFs are detected in the PDF pass

BUILD MARKER: 2026-10-27-bom-extractor-v50

ARCHITECTURE  (mirrors CLEAN_SWEEPER_BOM_EXTRACTOR.iLogicVb v18)
  Working file : G:\\Drawing Office\\SPELL CHECKER SCRIPT\\BOM EXTRACTOR TEMPLATES\\BOM Extractor Sweeper.xlsx
  Template     : same folder\\BOM EXTRACTOR_TEMP.xlsx  (always copied as base — old working file replaced each run)
  Named copy   : G:\\Common\\<PJ#####>*\\<subfolder containing "BOM">\\<proposed name>.xlsx
                 Subfolder "10 - BOM" is created automatically if none found.
  Rev          : auto-extracted from the first drawing's title block REV box
                 (falls back to "0" if the title block cannot be read)
  Prefix filter: only PDFs whose stem starts with the same PJ#####-SITE-AREA- prefix
                 as the first selected file are processed.
  At finish    : opens the BOM folder in Explorer, then opens the named copy in Excel.
                 Working file stays closed.

OUTPUT COLUMNS (fixed — matches iLogic v18 sheet layout)
  Rev | Item | QTY | Description | Specification

EXTRACTION APPROACH
  Uses the same BOM-detection logic as SpellCheckPDF_Word.py (proven on
  Inventor drawings):
    1. find_bom_headers()    — locates ITEM + QTY + DESCRIPTION header row
    2. extract_item_column() — finds item numbers (integers + sub-items 5a/5b)
    3. For each item row: scans header-row width and assigns words to columns

HOW TO RUN
  Double-click BomExtractor.bat
  OR:  python BomExtractorSweeper.py
"""

import sys
import subprocess
import os
import time
from pathlib import Path
from datetime import datetime

# ============================================================
#  DESKTOP LOG  — written every run so we can diagnose issues
# ============================================================
_LOG_PATH = Path(os.path.expandvars(r"%USERPROFILE%\Desktop\BomExtractor_log.txt"))

class _Tee:
    """Write to both stdout and a log file simultaneously."""
    def __init__(self, log_path):
        self._log = None
        try:
            self._log = open(log_path, "w", encoding="utf-8")
        except Exception:
            pass
        self._stdout = sys.__stdout__

    def write(self, text):
        # Suppress PyMuPDF's pymupdf_layout suggestion (informational only, not relevant)
        if "pymupdf_layout" in text:
            return
        try:
            self._stdout.write(text)
        except Exception:
            pass
        if self._log:
            try:
                self._log.write(text)
                self._log.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self._stdout.flush()
        except Exception:
            pass
        if self._log:
            try:
                self._log.flush()
            except Exception:
                pass

    def close(self):
        if self._log:
            try:
                self._log.close()
            except Exception:
                pass

_tee = _Tee(_LOG_PATH)
sys.stdout = _tee
sys.stderr = _tee

print(f"{'='*60}")
print(f"BOM Extractor log — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}")


def install_missing():
    import importlib
    packages = {
        "PyMuPDF": "fitz",
        "openpyxl": "openpyxl",
    }
    for pkg, imp in packages.items():
        try:
            importlib.import_module(imp)
            print(f"  {pkg}: already installed")
        except ImportError:
            print(f"  Installing {pkg} ...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg,
                     "--quiet", "--timeout", "15"],
                    stderr=subprocess.STDOUT,
                    timeout=60,
                )
                print(f"  {pkg}: installed OK")
            except subprocess.TimeoutExpired:
                print(f"  {pkg}: pip timed out — check network/proxy")
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"  {pkg}: pip failed (code {e.returncode})")
                sys.exit(1)


print("Checking dependencies...")
install_missing()
print("Dependencies ready.")

import os
import re
import shutil
import ctypes
import ctypes.wintypes as wintypes
import traceback
from pathlib import Path

import fitz  # PyMuPDF
print(f"  PyMuPDF version  : {fitz.version[0]} (fitz {fitz.version[1]})")

# ---------------------------------------------------------------------------
# Spec-band description-overflow reclaim
# ---------------------------------------------------------------------------
# Inventor BOM text flows left-to-right across column bands.  Words from a
# long description that overflow past the x=1916.2 divider land in the spec
# cell.  We reclaim them by finding the first "strong spec anchor" in the
# spec words and prepending everything before that anchor back to description.
#
# STRONG anchors — these are unambiguous spec starters; if text BEFORE them
# in the spec cell exists it must be description overflow:
#   • Part-number codes:  PJ…, JC…  (followed by a digit)
#   • Standards:          AS, ASTM, ASME, ISO, BS, DIN, EN  (+ digit/hyphen)
#   • Instrument tags:    2–5 uppercase letters, hyphen, digit  (FE-1, FIT-2…)
#   • Supply / note ref:  SUPPLIED, NOTE, NOT (SHOWN)
#
# WEAK anchors — materials/finishes that begin a spec on their own; they
# must NOT trigger a reclaim because no description overflow precedes them:
#   GALVAN*, STAINLESS, CARBON, NATURAL, RUBBER, NYLON, HDPE, PLAIN, QUICK,
#   BSP, PE, POLYETHYLENE, etc.
# Only when the FIRST matched anchor is STRONG and has index > 0 do we move
# the preceding words to description.

_SPEC_STRONG_ANCHOR = re.compile(
    r'^('
    r'PJ\d|JC\d'                           # project part-number codes
    r'|AS[\d\-\s]|ASTM|ASME|ISO|BS[\d\s]|DIN|EN[\d\-\s]'  # standards
    r'|SUPPLIED|NOT[\s\b]|NOTE\b'          # supply/note refs
    r'|[A-Z]{1,5}-\d'                      # instrument tags: FE-1, FIT-2, LIT-3
    r'|\d{2,3}-\d'                         # material grades: 18-8, 17-4, 316-L
    r')',
    re.IGNORECASE
)


def _reclaim_spec_overflow(desc_val: str, spec_val: str):
    """
    Move description-overflow words from the START of *spec_val* back to
    *desc_val*.

    Inventor renders BOM rows as a single horizontal text stream; long
    descriptions overflow the column divider, and the overflow words land at
    the beginning of the spec cell.  We identify the first strong spec anchor
    (a part number, standard, or instrument tag) and treat everything before
    it as description overflow.

    Returns (new_desc_val, new_spec_val).
    """
    if not spec_val:
        return desc_val, spec_val

    words = spec_val.split()
    if not words:
        return desc_val, spec_val

    # Find the first STRONG anchor word in the spec
    anchor_idx = None
    for i, w in enumerate(words):
        if _SPEC_STRONG_ANCHOR.match(w):
            anchor_idx = i
            break

    # No strong anchor found, or spec already starts with one — nothing to move
    if anchor_idx is None or anchor_idx == 0:
        return desc_val, spec_val

    # Everything before the anchor belongs to description
    overflow   = ' '.join(words[:anchor_idx])
    new_spec   = ' '.join(words[anchor_idx:])
    new_desc   = (desc_val + ' ' + overflow).strip() if desc_val else overflow
    return new_desc, new_spec

# ── Tesseract detection (needed for OCR fallback on SHX/rasterised PDFs) ──────
_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    # User-profile installs (common when no admin rights)
    os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "Tesseract-OCR", "tesseract.exe"),
    os.path.join(os.path.expandvars("%APPDATA%"), "Tesseract-OCR", "tesseract.exe"),
]
_TESSERACT_EXE = None
for _tp in _TESSERACT_PATHS:
    if os.path.isfile(_tp):
        _TESSERACT_EXE = _tp
        break

if _TESSERACT_EXE:
    # Tell PyMuPDF where tesseract lives
    os.environ.setdefault("TESSDATA_PREFIX",
                          str(Path(_TESSERACT_EXE).parent / "tessdata"))
    print(f"  Tesseract        : found at {_TESSERACT_EXE}")
    print(f"  OCR fallback     : ENABLED  (SHX/rasterised PDFs will be processed)")
else:
    print("  Tesseract        : NOT FOUND — OCR fallback DISABLED")
    print("    SHX / rasterised AutoCAD PDFs will be skipped.")
    print("    To enable OCR: install Tesseract from")
    print("    https://github.com/UB-Mannheim/tesseract/wiki")

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ============================================================
#  CONSTANTS
# ============================================================

HEADER_ROW_TOLERANCE_PT    = 3.0
COLUMN_MARGIN_PT           = 6.0
ROW_CLUSTER_MIN_GAP_PT     = 25.0
ROW_CLUSTER_GAP_MULTIPLIER = 3.0
SUBITEM_X_MARGIN_PT        = 20.0
DATA_ROW_Y_TOLERANCE_PT    = 4.5
COLUMN_CLUSTER_GAP_PT      = 8.0
BELOW_HEADER_MIN_PT        = 30.0  # column lines must extend this far below the header row
                                   # — filters out decorative borders confined to header cell height

ITEM_FULL_RE = re.compile(r"^(\d{1,3})([a-zA-Z]?)$")

# ── AutoCAD inverted-BOM detection ───────────────────────────────────────────
# AutoCAD BOMs have the header row at the BOTTOM and item rows ABOVE it.
# The ITEM/QTY columns are narrow and their header text is often unreadable
# after OCR (cell borders obscure it), so we anchor on DESCRIPTION + PART.
_ACAD_BOM_Y_FRAC       = 0.50   # header must be in lower half of page
_ACAD_BOM_X_FRAC       = 0.40   # header must be in right portion of page
_ACAD_DESC_LEFT_MARGIN = 80.0   # pt: description data starts this far LEFT of
                                 #     the DESCRIPTION header word's x0
# ─────────────────────────────────────────────────────────────────────────────

# Fixed paths — match iLogic v18
WORKING_FOLDER   = r"G:\Drawing Office\SPELL CHECKER SCRIPT\BOM EXTRACTOR TEMPLATES"
WORKING_FILENAME = "BOM Extractor Sweeper.xlsx"
TEMPLATE_FILENAME = "BOM EXTRACTOR_TEMP.xlsx"

# Log files (written to WORKING_FOLDER; one per source type)
LOG_FILE_PDF = "BomExtractorPDF_log.txt"
LOG_FILE_DWG = "BomExtractorDWG_log.txt"
LOG_FILE_MIX = "BomExtractor_log.txt"

# Named-copy search root
COMMON_ROOT = r"G:\Common"

BUILD_MARKER = "2026-10-28-bom-extractor-v83"


class _Tee:
    """Mirror stdout to a log file simultaneously."""
    def __init__(self, log_path):
        self._file   = open(log_path, "w", encoding="utf-8", errors="replace")
        self._stdout = sys.stdout
        sys.stdout   = self

    def write(self, data):
        self._stdout.write(data)
        self._file.write(data)

    def flush(self):
        self._stdout.flush()
        self._file.flush()

    def close(self):
        sys.stdout = self._stdout
        self._file.flush()
        self._file.close()

    # Forward anything else (isatty, fileno, etc.) to original stdout
    def __getattr__(self, name):
        return getattr(self._stdout, name)

# Output column order (fixed — matches iLogic v18 sheet)
OUT_COLS = ["Item", "QTY", "Description", "Specification"]

# Excel styling — matches iLogic v18 (Aptos Narrow, green banner)
_GREEN_FILL = PatternFill("solid", fgColor="92D050")   # RGB(146, 208, 80)
_THIN       = Side(border_style="thin", color="000000")
_BORDER     = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_THICK_LEFT = Border(left=Side(border_style="medium", color="000000"),
                     right=_THIN, top=_THIN, bottom=_THIN)

_FONT_HEADER = Font(name="Aptos Narrow", size=10, bold=True)
_FONT_BANNER = Font(name="Aptos Narrow", size=10, bold=True)
_FONT_DATA   = Font(name="Aptos Narrow", size=10)
_ALIGN_CTR   = Alignment(horizontal="center", vertical="center")
_ALIGN_LEFT  = Alignment(horizontal="left",   vertical="center")


# ============================================================
#  WINDOWS HELPERS
# ============================================================

def pick_files(title="Select drawing file(s) — hold Ctrl for multiple",
               filter_str=None):
    """
    Native Windows multi-select file picker.

    filter_str — raw OPENFILENAME filter string (NUL-separated pairs).
                 Defaults to PDF + DWG files.
    Returns a list of absolute path strings, or [] if cancelled.
    """
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

    if filter_str is None:
        filter_str = ("Drawing Files\0*.pdf;*.dwg\0"
                      "PDF Files\0*.pdf\0"
                      "AutoCAD DWG Files\0*.dwg\0"
                      "All Files\0*.*\0")

    ofn             = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.lpstrFilter = filter_str
    ofn.lpstrFile   = ctypes.cast(buf, ctypes.c_wchar_p)
    ofn.nMaxFile    = MAX
    ofn.lpstrTitle  = title
    ofn.Flags       = (OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST |
                       OFN_ALLOWMULTISELECT | OFN_EXPLORER)

    if not ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return []

    parts, current = [], []
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
    if len(parts) == 1:
        return [parts[0]]
    folder = parts[0]
    return [str(Path(folder) / f) for f in parts[1:]]


def pick_pdfs():
    """Shorthand: pick PDF files only (first-pass selection)."""
    return pick_files(
        title="Select drawing PDF(s) — hold Ctrl for multiple",
        filter_str=("PDF Files\0*.pdf\0All Files\0*.*\0"),
    )


def pick_dwgs_for_shx(shx_names):
    """
    Second-pass picker: user points at DWG files for the SHX drawings.
    The caller filters the returned list to only stems in shx_names.
    """
    joined = ", ".join(shx_names)
    # Truncate display list if very long
    display = joined if len(joined) <= 200 else joined[:197] + "…"
    title = (f"Select AutoCAD DWG file(s) for SHX drawings: {display}"
             " — you can select all DWGs; only the needed ones will be used")
    return pick_files(
        title=title,
        filter_str=("AutoCAD DWG Files\0*.dwg\0All Files\0*.*\0"),
    )


def show_message(title, msg, error=False):
    icon = 0x10 if error else 0x40
    ctypes.windll.user32.MessageBoxW(0, msg, title, icon)


def open_in_explorer(folder):
    """Open a folder in Windows Explorer."""
    try:
        os.startfile(str(folder))
    except Exception:
        pass


def open_in_excel(file_path):
    """Open a file in Excel (reuse running instance if available)."""
    try:
        os.startfile(str(file_path))
    except Exception:
        pass


# ============================================================
#  DRAWING PREFIX + REV HELPERS  (mirrors iLogic v18)
# ============================================================

def get_drawing_prefix(stem):
    """
    Returns "PJ00145-GTA-3280-" (everything up to and including the third dash).
    Falls back to the full stem if fewer than 3 dashes present.
    """
    parts = stem.split("-")
    if len(parts) >= 3:
        return f"{parts[0]}-{parts[1]}-{parts[2]}-"
    return stem


def proposed_bom_name(first_pdf_stem, rev, source_suffix=""):
    """
    PJ00143-GTA-3431-6-00310  ->  PJ00143-GTA-3431-BOM100001_A_PDF
    source_suffix: "_PDF", "_DWG", or "" (mixed / unspecified)
    """
    parts = first_pdf_stem.split("-")
    if len(parts) >= 3:
        prefix = f"{parts[0]}-{parts[1]}-{parts[2]}"
    else:
        prefix = first_pdf_stem
    return f"{prefix}-BOM100001_{rev}_TEMP{source_suffix}"


def is_fabrication(drawing_no):
    """
    4xx series: 3rd-from-last character is "4".
    e.g. PJ00143-GTA-3431-6-00413  ->  True
    """
    if len(drawing_no) < 3:
        return False
    return drawing_no[len(drawing_no) - 3] == "4"


# ============================================================
#  BOM FOLDER LOOKUP  (mirrors iLogic v18 FindOrCreateBomFolder)
# ============================================================

def find_or_create_bom_folder(first_pdf_stem):
    """
    1. Extract project prefix ("PJ00143") from the drawing stem.
    2. Find first subfolder of G:\\Common whose name starts with that prefix.
    3. Inside that folder, find a subfolder whose name contains "BOM".
    4. If no BOM subfolder exists, create "10 - BOM".
    Returns the BOM folder path, or "" if G:\\Common not found or no project match.
    """
    common = Path(COMMON_ROOT)
    if not common.exists():
        return ""

    # Extract project code: everything before the first dash
    dash = first_pdf_stem.find("-")
    prefix = first_pdf_stem[:dash] if dash > 0 else first_pdf_stem

    project_folder = None
    try:
        for d in sorted(common.iterdir()):
            if d.is_dir() and d.name.upper().startswith(prefix.upper()):
                project_folder = d
                break
    except Exception:
        return ""

    if not project_folder:
        return ""

    # Find subfolder containing "BOM"
    bom_folder = None
    try:
        for sub in sorted(project_folder.iterdir()):
            if sub.is_dir() and "BOM" in sub.name.upper():
                bom_folder = sub
                break
    except Exception:
        pass

    if not bom_folder:
        bom_folder = project_folder / "10 - BOM"
        try:
            bom_folder.mkdir(exist_ok=True)
        except Exception:
            return ""

    return str(bom_folder)


def pick_copy_folder(start_folder):
    """Windows folder picker — fallback when auto-locate fails."""
    try:
        from win32gui import GetDesktopWindow  # type: ignore
    except ImportError:
        pass

    # Use shell32 SHBrowseForFolder
    class BROWSEINFOW(ctypes.Structure):
        _fields_ = [
            ("hwndOwner",      wintypes.HWND),
            ("pidlRoot",       ctypes.c_void_p),
            ("pszDisplayName", ctypes.c_wchar_p),
            ("lpszTitle",      ctypes.c_wchar_p),
            ("ulFlags",        wintypes.UINT),
            ("lpfn",           ctypes.c_void_p),
            ("lParam",         ctypes.c_longlong),
            ("iImage",         ctypes.c_int),
        ]

    BIF_RETURNONLYFSDIRS   = 0x0001
    BIF_NEWDIALOGSTYLE     = 0x0040
    BFFM_INITIALIZED       = 1
    BFFM_SETSELECTIONW     = 0x400 + 103

    selected = ctypes.create_unicode_buffer(260)
    bi = BROWSEINFOW()
    bi.lpszTitle = "Select folder for the completed EBOM copy"
    bi.ulFlags   = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE

    shell32 = ctypes.windll.shell32
    pidl = shell32.SHBrowseForFolderW(ctypes.byref(bi))
    if not pidl:
        return ""
    shell32.SHGetPathFromIDListW(pidl, selected)
    ctypes.windll.ole32.CoTaskMemFree(pidl)
    return selected.value


def save_named_copy(working_path, first_pdf_stem, rev, source_suffix=""):
    """
    Copy working file to BOM folder with proposed name.
    Mirrors iLogic v18 SaveNamedCopy.
    source_suffix: "_PDF", "_DWG", or "" appended before .xlsx.
    Returns the destination path, or "" if user cancels.
    """
    if not Path(working_path).exists():
        return ""

    bom_folder = find_or_create_bom_folder(first_pdf_stem)
    if not bom_folder:
        show_message(
            "BOM Extractor — folder not found",
            f"Could not locate a project folder under {COMMON_ROOT} for this drawing.\n"
            "Please choose the destination folder manually."
        )
        bom_folder = pick_copy_folder(str(Path(working_path).parent))
        if not bom_folder:
            return ""

    proposed = proposed_bom_name(first_pdf_stem, rev, source_suffix) + ".xlsx"
    print(f"\n  EBOM file name : {proposed}")
    chosen = proposed   # auto-accept — no confirmation prompt

    # Try the primary filename; if it is open in Excel try _1, _2, … so the
    # user can leave the previous result open for side-by-side comparison.
    _base = Path(bom_folder) / chosen          # e.g.  …/PJ00197-…_A_TEMP_PDF.xlsx
    _stem = _base.stem                         # without .xlsx
    for _suffix in [""] + [f"_{i}" for i in range(1, 10)]:
        _candidate = _base.with_stem(_stem + _suffix) if _suffix else _base
        try:
            shutil.copy2(working_path, str(_candidate))
            if _suffix:
                print(f"  Named copy saved: {_candidate}  (primary was open in Excel)")
            else:
                print(f"  Named copy saved: {_candidate}")
            return str(_candidate)
        except PermissionError:
            continue
        except Exception as e:
            print(f"  WARNING: could not save named copy — {e}")
            return ""
    msg = (f"Could not save named copy — all candidate filenames are open in Excel.\n"
           f"Please close one of them and run again.\n\nBase: {_base}")
    print(f"  WARNING: {msg}")
    show_message("BOM Extractor — file in use", msg, error=True)
    return ""


# ============================================================
#  OCR HELPER
# ============================================================

def get_page_words(page, allow_ocr=True):
    """
    Return the word list for *page* using page.get_text("words").

    If the native text layer is empty AND tesseract is available AND
    allow_ocr is True, fall back to PyMuPDF's built-in OCR engine
    (page.get_textpage_ocr) which calls tesseract internally.

    Returns (words, ocr_used) where:
      words    — list of (x0,y0,x1,y1,text,...) tuples (may be empty)
      ocr_used — True if the OCR path was taken
    """
    words = page.get_text("words")
    if words:
        return words, False

    if not allow_ocr or not _TESSERACT_EXE:
        return [], False

    try:
        # flags=3  →  TEXT_PRESERVE_WHITESPACE | TEXT_PRESERVE_LIGATURES
        tp    = page.get_textpage_ocr(flags=3, dpi=300, full=False)
        words = page.get_text("words", textpage=tp)
        return words, True
    except Exception as exc:
        print(f"      [OCR error: {exc}]")
        return [], False


# ============================================================
#  BOM HEADER DETECTION  (same as SpellCheckPDF_Word.py)
# ============================================================

def _wcy(w):
    return (w[1] + w[3]) / 2


def _norm(text):
    return text.strip().upper().replace(" ", "").replace(".", "")


def find_bom_headers(words):
    """
    Locate BOM header rows. Requires ITEM + QTY + DESCRIPTION
    all within HEADER_ROW_TOLERANCE_PT vertically.
    Accepts variants: ITEMNO, QUANTITY/QTY, DESCRIPTION/DESC.
    Returns list of ITEM word tuples (one per BOM on the page).
    """
    item_words = [w for w in words if _norm(w[4]) in {"ITEM", "ITEMNO"}]
    qty_words  = [w for w in words if _norm(w[4]) in {"QTY", "QUANTITY"}]
    desc_words = [w for w in words if _norm(w[4]) in {"DESCRIPTION", "DESC"}]

    headers = []
    for iw in item_words:
        iy = _wcy(iw)
        if not any(abs(_wcy(q) - iy) <= HEADER_ROW_TOLERANCE_PT for q in qty_words):
            continue
        if any(abs(_wcy(d) - iy) <= HEADER_ROW_TOLERANCE_PT for d in desc_words):
            headers.append(iw)
    return headers


def find_bom_header_autocad(words, pw, ph):
    """
    AutoCAD inverted-BOM fallback header detector.

    AutoCAD BOMs place the header row at the BOTTOM of the BOM table
    (items are above it).  The ITEM and QTY cells are narrow and their
    text is often missing from OCR output due to cell border interference.
    This function anchors on DESCRIPTION + PART/SPECIFICATION, which are
    wider cells reliably captured by OCR.

    Searches in the lower-right quadrant of the page where the title block
    and BOM table live in AutoCAD landscape drawings.

    Returns a dict with header geometry, or None if not found:
        {
          "header_y":  float,  # y-centre of the header row
          "desc_x0":   float,  # left edge of DESCRIPTION header word
          "part_x0":   float,  # left edge of PART / SPECIFICATION word
          "mass_x0":   float,  # left edge of MASS column (or pw if absent)
        }
    """
    # ── Step 1: locate the DESCRIPTION header word ───────────────────────────
    # OCR of AutoCAD SHX fonts can garble or truncate header words due to cell
    # border interference.  We try exact match first, then broaden progressively.

    def _in_bom_zone(w):
        """Word is in the lower-right quadrant where the BOM header lives."""
        return (_wcy(w) > ph * _ACAD_BOM_Y_FRAC
                and (w[0] + w[2]) / 2 > pw * _ACAD_BOM_X_FRAC)

    # Pass 1 — exact normalised match
    desc_cands = [w for w in words
                  if _norm(w[4]) in {"DESCRIPTION", "DESC"} and _in_bom_zone(w)]

    # Pass 2 — startswith "DESC" (catches truncated OCR like "DESCRIPT", "DESCRI")
    if not desc_cands:
        desc_cands = [w for w in words
                      if _norm(w[4]).startswith("DESC") and _in_bom_zone(w)]

    # Pass 3 — use PART or SPECIFICATION as the primary anchor instead.
    # If DESCRIPTION is completely unreadable, PART / SPEC are in a wider cell
    # and may survive OCR better.
    part_anchor = None
    if not desc_cands:
        part_anchor_cands = [
            w for w in words
            if _norm(w[4]) in {"PART", "PARTNO", "SPECIFICATION", "SPEC"}
            and _in_bom_zone(w)
        ]
        if part_anchor_cands:
            part_anchor = max(part_anchor_cands, key=lambda w: _wcy(w))

    if not desc_cands and part_anchor is None:
        # ── Diagnostics: show lower-right words so detection can be tuned ────
        lr_words = sorted(
            [w for w in words if _in_bom_zone(w)],
            key=lambda w: _wcy(w), reverse=True
        )
        print(f"      [AutoCAD] DESCRIPTION not found in lower-right quadrant")
        print(f"      [AutoCAD] lower-right words (bottom 30 by y): "
              f"{[w[4] for w in lr_words[:30]]}")
        return None

    # ── Step 2: fix the header y and column boundaries ────────────────────────
    if desc_cands:
        # Use the DESCRIPTION word nearest the page bottom as the anchor.
        desc_w   = max(desc_cands, key=lambda w: _wcy(w))
        header_y = _wcy(desc_w)
        desc_x0  = desc_w[0]

        # PART / SPECIFICATION: must be to the right of DESCRIPTION, same row.
        part_cands = [
            w for w in words
            if _norm(w[4]) in {"PART", "PARTNO", "SPECIFICATION", "SPEC"}
            and abs(_wcy(w) - header_y) <= HEADER_ROW_TOLERANCE_PT
            and w[0] > desc_w[2]
        ]
        part_x0 = (min(part_cands, key=lambda w: w[0])[0]
                   if part_cands else desc_w[2] + 20.0)
    else:
        # PART anchor fallback — derive desc_x0 as a fixed offset to its left.
        desc_w   = None
        header_y = _wcy(part_anchor)
        part_x0  = part_anchor[0]
        desc_x0  = max(0.0, part_x0 - 120.0)   # estimate description column start

    # MASS column start — look for "MASS" or "(EA)" on the same header row.
    mass_cands = [
        w for w in words
        if _norm(w[4]) in {"MASS", "(EA)", "EA"}
        and abs(_wcy(w) - header_y) <= HEADER_ROW_TOLERANCE_PT
        and w[0] > part_x0
    ]
    mass_x0 = min((w[0] for w in mass_cands), default=pw)

    print(f"      [AutoCAD] header_y={header_y:.1f}  desc_x0={desc_x0:.1f}"
          f"  part_x0={part_x0:.1f}  mass_x0={mass_x0:.1f}")

    return {
        "header_y": header_y,
        "desc_x0":  desc_x0,
        "part_x0":  part_x0,
        "mass_x0":  mass_x0,
    }


# ============================================================
#  TITLE BLOCK INFO  (rev + drawing description)
# ============================================================

# Fraction of page width: broad left-edge filter; the SCALE+REV pair check is the real guard.
_TB_X_FRAC = 0.30
# Fraction of page height: title block is in the lower portion of the page.
_TB_Y_FRAC = 0.40

def extract_title_block_info(doc):
    """
    Extract the REV value and the drawing description (last 1-2 text lines just
    above the SCALE / DRAWING NUMBER row) from the title block.

    Anchor strategy: find the row that contains BOTH "SCALE" and "REV" at the
    same y-level (they are adjacent column headers in the title block).  This
    distinguishes the real title-block SCALE from stray text such as "DO NOT
    SCALE" which has no matching REV header at the same y.

    Returns
    -------
    (rev_str, description_str)
      rev_str        : e.g. "0", "A", "1A" -- empty string if not found
      description_str: e.g. "LOWER FLOTATION GENERAL ARRANGEMENT" -- empty string
                       if not found; the two lines are space-joined on one line
    """
    for page_num in range(min(2, len(doc))):
        page = doc[page_num]
        words, ocr_used = get_page_words(page)
        if not words:
            continue
        if ocr_used:
            print(f"    Title block page {page_num + 1}: OCR fallback — {len(words)} words found")

        pw = page.rect.width
        ph = page.rect.height

        # ── 1. Locate the SCALE anchor word ───────────────────────────────
        # Require the SCALE word to have a REV word at the same y (+/-6 pt) and
        # to its right.  This filters out "DO NOT SCALE" and other stray SCALE
        # occurrences that do not belong to the title-block column-header row.
        scale_cands = [
            w for w in words
            if w[4].strip().upper() == "SCALE"
            and _wcy(w) > ph * _TB_Y_FRAC
            and (w[0] + w[2]) / 2 > pw * _TB_X_FRAC
        ]
        rev_cands = [
            w for w in words
            if w[4].strip().upper() == "REV"
            and _wcy(w) > ph * _TB_Y_FRAC
            and (w[0] + w[2]) / 2 > pw * _TB_X_FRAC
        ]

        anc     = None
        rev_hdr = None
        for sw in sorted(scale_cands, key=lambda w: _wcy(w)):
            for rw in sorted(rev_cands, key=lambda w: _wcy(w)):
                if abs(_wcy(sw) - _wcy(rw)) <= 6.0 and rw[0] > sw[2]:
                    anc     = sw
                    rev_hdr = rw
                    break
            if anc:
                break

        if anc is None:
            continue

        anc_y = _wcy(anc)

        # ── 2. REV value ──────────────────────────────────────────────────
        # rev_hdr is already the confirmed "REV" column header; look for its
        # value in the row immediately below.
        rev_str = ""
        if rev_hdr:
            rh    = rev_hdr
            rh_cx = (rh[0] + rh[2]) / 2
            rh_hw = (rh[2] - rh[0]) / 2 + COLUMN_MARGIN_PT + 10

            rev_vals = [
                w for w in words
                if abs((w[0] + w[2]) / 2 - rh_cx) <= rh_hw
                and _wcy(w) > anc_y + 2
                and _wcy(w) < anc_y + 55
                and 1 <= len(w[4].strip()) <= 3
                and w[4].strip().upper() not in {"REV", "SHT", "A1", "A0", "A3", "A4"}
            ]
            rev_vals.sort(key=lambda w: _wcy(w))
            if rev_vals:
                rev_str = rev_vals[0][4].strip()

        # ── 3. Description lines ──────────────────────────────────────────
        # Words in the title block right section, ABOVE the SCALE row.
        # Use max(anchor_x0 - 30, page_width * 0.30) as the left boundary
        # so we stay in the right section and exclude the signature columns.
        desc_x0 = max(anc[0] - 30.0, pw * _TB_X_FRAC)

        desc_cands = [
            w for w in words
            if w[0] >= desc_x0
            and _wcy(w) < anc_y - 3
            and _wcy(w) > ph * _TB_Y_FRAC
            and w[4].strip()
        ]

        if not desc_cands:
            return rev_str, ""

        # Cluster into text lines by y-proximity
        desc_cands.sort(key=lambda w: (_wcy(w), w[0]))
        line_groups = []
        cur = [desc_cands[0]]
        for dw in desc_cands[1:]:
            if abs(_wcy(dw) - _wcy(cur[-1])) <= 4.0:
                cur.append(dw)
            else:
                line_groups.append(cur)
                cur = [dw]
        if cur:
            line_groups.append(cur)

        # Take the last 2 lines (immediately above SCALE = the short description lines).
        n_take = min(2, len(line_groups))
        desc_text = " ".join(
            " ".join(w[4].strip() for w in sorted(ln, key=lambda w: w[0]))
            for ln in line_groups[-n_take:]
        )

        return rev_str, desc_text.strip()

    return "", ""


# ============================================================
#  ITEM COLUMN EXTRACTION
# ============================================================

def extract_item_column(words, header_word, max_y=None, above=False):
    """
    Find all item-number words in the ITEM column x-band.
    Accepts integers (1–999) and sub-items (5a, 5b, 5c).
    Row-clusters to discard stray digits elsewhere on the page.
    Returns list sorted by y ascending.

    max_y : optional upper y-ceiling (exclusive, below-mode only).
            When multiple BOM tables exist on the same page pass the
            y-coordinate of the NEXT header so each BOM only collects
            its own rows.
    above : when True, collect rows ABOVE the header instead of below
            (AutoCAD / inverted-BOM convention: header at bottom).
    """
    hx0, hx1 = header_word[0], header_word[2]
    header_y  = _wcy(header_word)

    # Left margin uses SUBITEM_X_MARGIN_PT so indented sub-items (5a, 5b…) are
    # captured even if the sub-item letter pushes the word slightly left of the
    # header text.
    # Right margin is COLUMN_MARGIN_PT only — NOT SUBITEM_X_MARGIN_PT.
    # Using the full SUBITEM_X_MARGIN_PT on the right extends col_x1 far enough
    # to capture the QTY column's text, whose x-centre sits only ~19 pt right of
    # the ITEM header's right edge.  QTY values (e.g. 32, 64, 84, 168) match
    # ITEM_FULL_RE and become spurious "item numbers", causing duplicate rows.
    col_x0 = hx0 - COLUMN_MARGIN_PT - SUBITEM_X_MARGIN_PT
    col_x1 = hx1 + COLUMN_MARGIN_PT          # tight right boundary — keeps QTY out

    col_words, seen = [], set()
    for w in words:
        wy = _wcy(w)
        if above:
            # Inverted BOM: items are ABOVE the header row.
            if wy >= header_y:
                continue
        else:
            # Normal BOM: items are BELOW the header row.
            # A stray digit in the title-block or revision table above the BOM
            # (e.g. a rogue "9" above item 1) would otherwise claim an item slot
            # and push the real item 9 row off the y-grid.
            if wy <= header_y:
                continue
            # If a ceiling was provided (next BOM header's y), stop before it.
            if max_y is not None and wy >= max_y:
                continue
        text = w[4].strip()
        if not ITEM_FULL_RE.match(text):
            continue
        cx = (w[0] + w[2]) / 2
        if not (col_x0 <= cx <= col_x1):
            continue
        pos_key = (text, round(w[0], 1), round(w[1], 1))
        if pos_key in seen:
            continue
        seen.add(pos_key)
        col_words.append(w)

    col_words.sort(key=lambda w: w[1])

    if len(col_words) > 2:
        gaps       = [col_words[i+1][1] - col_words[i][1] for i in range(len(col_words)-1)]
        median_gap = sorted(gaps)[len(gaps) // 2]
        max_gap    = max(ROW_CLUSTER_MIN_GAP_PT, median_gap * ROW_CLUSTER_GAP_MULTIPLIER)
        runs       = [[col_words[0]]]
        for w, gap in zip(col_words[1:], gaps):
            if gap <= max_gap:
                runs[-1].append(w)
            else:
                runs.append([w])
        col_words = max(runs, key=len)

    # Dedup by item text — keep the first (lowest-y) occurrence.
    # Duplicate item numbers in balloon callouts or revision clouds elsewhere
    # on the drawing can survive the cluster filter if they share the main cluster.
    text_seen: dict = {}
    for w in col_words:
        t = w[4].strip()
        if t not in text_seen:
            text_seen[t] = w
    col_words = sorted(text_seen.values(), key=lambda w: w[1])

    return col_words


def extract_inverted_bom_rows(words, hinfo):
    """
    Extract BOM rows from an AutoCAD inverted BOM (header at bottom,
    items above it).  Uses column geometry from find_bom_header_autocad().

    Three-band column layout (cx = word x-centre):
      cx <  item_qty_split  (= desc_x0 - _ACAD_DESC_LEFT_MARGIN)  → ITEM band
      item_qty_split <= cx < qty_desc_split  (= desc_x0)           → QTY band
      qty_desc_split <= cx < part_x0                               → DESCRIPTION band
      part_x0        <= cx < mass_x0                               → SPECIFICATION band
      cx >= mass_x0                                                 → MASS (ignored)

    QTY and DESCRIPTION are separate bands so that short numeric QTY values
    (e.g. "12") that sit between the ITEM column and the description column
    are not swallowed into the description text.

    Returns a list of row dicts ordered item-1-first (closest to header):
        {"item_text": str, "item_y": float, "cells": [item, qty, desc, spec]}
    """
    header_y = hinfo["header_y"]
    desc_x0  = hinfo["desc_x0"]
    part_x0  = hinfo["part_x0"]
    mass_x0  = hinfo["mass_x0"]

    # Column band split points.
    # item_qty_split: left edge of QTY column data (ITEM data is to its left).
    # qty_desc_split: left edge of DESCRIPTION data; equals the DESCRIPTION
    #   header word x0 — QTY values sit between item_qty_split and here.
    item_qty_split = desc_x0 - _ACAD_DESC_LEFT_MARGIN   # ≈ desc_x0 - 80
    qty_desc_split = desc_x0                             # description data starts here

    # Left edge of the entire BOM band (ITEM column starts here).
    bom_x0 = max(0.0, item_qty_split - 200.0)

    # Collect all words above the header row that fall within the BOM x-range.
    bom_words = [
        w for w in words
        if _wcy(w) < header_y - HEADER_ROW_TOLERANCE_PT
        and w[2] > bom_x0
        and w[0] < mass_x0
        and w[4].strip()
    ]
    if not bom_words:
        return []

    # ── Group words into horizontal rows by y-proximity ──────────────────────
    bom_words.sort(key=lambda w: _wcy(w))
    rows_by_y: list = [[bom_words[0]]]
    for w in bom_words[1:]:
        if abs(_wcy(w) - _wcy(rows_by_y[-1][0])) <= HEADER_ROW_TOLERANCE_PT:
            rows_by_y[-1].append(w)
        else:
            rows_by_y.append([w])

    # Sort rows closest-to-header first (descending y = largest y first).
    rows_by_y.sort(key=lambda row: _wcy(row[0]), reverse=True)

    # ── Pre-filter: remove rows with no content in desc or spec bands ─────────
    # OCR noise tokens that land only in the item/qty band create "ghost" rows
    # at intermediate y-values between the BOM and the drawing notes section.
    # These ghost rows break the gap filter by splitting one large BOM-to-notes
    # gap into several smaller sub-threshold gaps.  Removing them first exposes
    # the true gap and lets the adaptive filter cut correctly.
    def _has_desc_or_spec_content(row_words):
        return any(
            (w[0] + w[2]) / 2 >= qty_desc_split and len(w[4].strip()) >= 2
            for w in row_words
        )
    rows_by_y = [r for r in rows_by_y if _has_desc_or_spec_content(r)]

    # ── Adaptive gap filter ───────────────────────────────────────────────────
    # BOM item rows are tightly and evenly spaced (~8 pt on a standard A1
    # AutoCAD drawing).  The gap to the drawing-notes section is much larger
    # (~30 pt).  We use the minimum of the first four observed inter-row gaps
    # as the "typical BOM spacing" and stop at the first gap that is 1.5× that
    # value (floor 10 pt).  This adapts to different drawing scales and is far
    # more robust than a fixed 25 pt constant.
    if len(rows_by_y) > 2:
        ys      = [_wcy(r[0]) for r in rows_by_y]   # descending
        gaps_up = [ys[i] - ys[i + 1] for i in range(len(ys) - 1)]
        sample  = sorted(gaps_up[:min(4, len(gaps_up))])
        min_bom = sample[0] if sample else 8.0
        max_gap = max(10.0, min_bom * 1.5)
        cut = len(rows_by_y)
        for i, g in enumerate(gaps_up):
            if g > max_gap:
                cut = i + 1
                break
        print(f"      [AutoCAD] gap filter: min_gap={min_bom:.1f}pt  "
              f"max_gap={max_gap:.1f}pt  rows={len(rows_by_y)} → cut={cut}")
        rows_by_y = rows_by_y[:cut]

    # ── Extract cells from each row ───────────────────────────────────────────
    extracted    = []
    _NOISE_RE    = re.compile(r"[\[\](){}<>|]")
    for seq_num, row_words in enumerate(rows_by_y, start=1):
        cx_of = lambda w: (w[0] + w[2]) / 2  # noqa: E731

        item_band = sorted([w for w in row_words if cx_of(w) <  item_qty_split],
                           key=lambda w: w[0])
        qty_band  = sorted([w for w in row_words
                            if item_qty_split <= cx_of(w) < qty_desc_split],
                           key=lambda w: w[0])
        desc_band = sorted([w for w in row_words
                            if qty_desc_split <= cx_of(w) < part_x0],
                           key=lambda w: w[0])
        spec_band = sorted([w for w in row_words
                            if part_x0        <= cx_of(w) < mass_x0],
                           key=lambda w: w[0])

        desc_text = " ".join(w[4].strip() for w in desc_band)
        spec_text = " ".join(w[4].strip() for w in spec_band)

        if not desc_text and not spec_text:
            continue

        # ── Item number (item_band) ───────────────────────────────────────────
        item_text = ""
        for w in item_band:
            clean = _NOISE_RE.sub("", w[4].strip()).strip()
            if re.match(r"^\d{1,3}[a-zA-Z]?$", clean) and not item_text:
                item_text = clean

        # ── QTY (qty_band): first short integer token ─────────────────────────
        qty_text = ""
        for w in qty_band:
            clean = _NOISE_RE.sub("", w[4].strip()).strip()
            if re.match(r"^\d{1,4}$", clean) and not qty_text:
                qty_text = clean

        # Fall back to sequential position if OCR missed the item number.
        item_found = bool(item_text)   # True when an actual BOM digit was found
        if not item_text:
            item_text = str(seq_num)

        extracted.append({
            "item_text":  item_text,
            "item_y":     _wcy(row_words[0]),
            "item_found": item_found,
            "cells":      [item_text, qty_text, desc_text, spec_text],
        })

    # ── Merge wrapped continuation lines into their parent item row ───────────
    # A BOM cell whose spec or desc wraps to a second physical line creates a
    # new entry in rows_by_y (different y-coord, no item digit).  After
    # sorting descending-y (header first), a continuation line always sits
    # ONE slot BEFORE its parent item: because the second line is physically
    # below the first (y_cont = y_item + line_height > y_item), it sorts to a
    # higher position in the descending list — i.e. it comes just before the
    # parent item row.  Walk forward: when a row has no real item number,
    # append its spec/desc text to the NEXT row and discard the orphan.
    _cont_merged: list = []
    _ci = 0
    while _ci < len(extracted):
        _row = extracted[_ci]
        if not _row["item_found"] and _ci + 1 < len(extracted):
            # Continuation row — fold its content into the next item row.
            _nxt = extracted[_ci + 1]
            _cs  = _row["cells"][3]   # continuation spec text
            _cd  = _row["cells"][2]   # continuation desc text (rare)
            if _cs:
                _nxt["cells"][3] = (_nxt["cells"][3] + " " + _cs).strip()
            if _cd:
                _nxt["cells"][2] = (_nxt["cells"][2] + " " + _cd).strip()
            print(f"      [AutoCAD] cont-merge: "
                  f"spec={_cs!r}  desc={_cd!r} "
                  f"→ item {_nxt['item_text']!r}")
        else:
            _cont_merged.append(_row)
        _ci += 1
    extracted = _cont_merged

    return extracted


# ============================================================
#  COLUMN HEADER DETECTION
# ============================================================

def get_header_row_words(words, header_word):
    hy  = _wcy(header_word)
    row = [w for w in words if abs(_wcy(w) - hy) <= HEADER_ROW_TOLERANCE_PT]
    row.sort(key=lambda w: w[0])
    return row


def cluster_into_columns(header_row_words):
    """
    Group header words into column definitions (fallback when no vector lines found).

    Band boundary strategy (gap-based):
    ─ Inventor BOMs mix narrow columns (ITEM, QTY, MASS) whose header text nearly
      fills the column, with wide columns (DESCRIPTION, SPEC) whose header text is
      CENTRED — so the header x0 is far to the right of where data actually starts.
    ─ A large gap (> GAP_WIDE_PT) between consecutive headers signals that the
      LEFT column is narrow and the RIGHT column is wide.
    ─ For narrow columns:  bx1 = col_x1 + COLUMN_MARGIN_PT  (tight right edge)
    ─ For wide columns:    bx0 = prev_col_x1                (starts right after prev)
    ─ Adjacent narrow columns use midpoint as before.
    """
    GAP_WIDE_PT = 35.0   # gap this large → left col is narrow, right col is wide

    if not header_row_words:
        return []
    groups, grp = [], [header_row_words[0]]
    for w in header_row_words[1:]:
        if w[0] - grp[-1][2] <= COLUMN_CLUSTER_GAP_PT:
            grp.append(w)
        else:
            groups.append(grp)
            grp = [w]
    groups.append(grp)

    clusters = [{"name": " ".join(ww[4].strip() for ww in g),
                 "x0": g[0][0], "x1": g[-1][2]} for g in groups]

    result = []
    for i, col in enumerate(clusters):
        prev_gap = (col["x0"] - clusters[i-1]["x1"]) if i > 0 else 0
        next_gap = (clusters[i+1]["x0"] - col["x1"]) if i + 1 < len(clusters) else 0

        # ── Left boundary ──────────────────────────────────────────────────
        if i == 0:
            bx0 = col["x0"] - COLUMN_CLUSTER_GAP_PT
        elif prev_gap > GAP_WIDE_PT:
            # Large gap on left → previous col was narrow; this wide col starts
            # right at the previous header's right edge (= actual column boundary)
            bx0 = clusters[i-1]["x1"]
        else:
            bx0 = (clusters[i-1]["x1"] + col["x0"]) / 2

        # ── Right boundary ─────────────────────────────────────────────────
        if i + 1 >= len(clusters):
            bx1 = col["x1"] + 500
        elif next_gap > GAP_WIDE_PT:
            col_width = col["x1"] - col["x0"]
            if col_width > GAP_WIDE_PT:
                # Wide column (e.g. DESCRIPTION) followed by another wide column
                # (e.g. PART No./SPEC).  Both have centred headers so the gap
                # between their header texts is large — but the data in this
                # column can extend well past its header's right edge.
                # Use the midpoint of the gap so data words aren't clipped.
                bx1 = (col["x1"] + clusters[i+1]["x0"]) / 2
            else:
                # Narrow column (e.g. QTY) before a wide column.
                # Keep the band tight so description data that starts just after
                # does NOT land in this column's band.
                bx1 = col["x1"] + COLUMN_MARGIN_PT
        else:
            bx1 = (col["x1"] + clusters[i+1]["x0"]) / 2

        result.append({**col, "band_x0": bx0, "band_x1": bx1})
    return result


def get_bom_column_dividers(page, header_y, hrow=None, tolerance=15):
    """
    Find vertical table-line x-positions that bound BOM columns.

    Two filters keep the divider count clean:
      1. The path must start at/above the header AND extend BELOW_HEADER_MIN_PT below it.
         Real column lines span the whole table height; decorative borders around header
         cell text only span ~one row height and are excluded by this test.
      2. (When hrow is supplied) only paths whose x-centre lies within the BOM table's
         x-footprint (derived from the header word positions) are kept — this removes
         drawing-border and title-block lines that happen to cross the header y.

    Returns a sorted, deduplicated list of x-coordinates, or [] if < 3 found.
    """
    # Derive BOM x-range from the header words
    bom_x0 = bom_x1 = None
    if hrow:
        bom_x0 = min(w[0] for w in hrow) - 50
        bom_x1 = max(w[2] for w in hrow) + 50

    xs = set()
    n_paths = n_checked = 0
    try:
        for path in page.get_drawings():
            n_paths += 1
            r = path["rect"]
            # Must start above/at header and continue meaningfully below it
            if r.y0 > header_y + tolerance:
                continue
            if r.y1 < header_y + BELOW_HEADER_MIN_PT:
                continue
            if r.height < 8:
                continue
            n_checked += 1
            # Restrict to the BOM table x-footprint
            cx = (r.x0 + r.x1) / 2
            if bom_x0 is not None and not (bom_x0 <= cx <= bom_x1):
                continue
            if r.width < 3:
                xs.add(round(cx, 1))
            elif r.width > 5:
                xs.add(round(r.x0, 1))
                xs.add(round(r.x1, 1))
    except Exception as e:
        print(f"    [vector: get_drawings() error: {e}]")

    merged = []
    for x in sorted(xs):
        if not merged or x - merged[-1] > 2:
            merged.append(x)

    status = "using them" if len(merged) >= 3 else "fallback to heuristic"
    print(f"    [vector: {n_paths} paths, {n_checked} pass height+x filter, "
          f"{len(merged)} dividers → {status}]")
    if merged:
        print(f"    [dividers: {merged}]")
    return merged


def build_columns_from_dividers(dividers, header_row_words):
    """
    Build column band definitions from vertical divider x-positions.
    Each pair of adjacent dividers forms one band.

    Merged-header fix (Inventor PDFs):
      Inventor prints "ITEM QTY" as one merged text object in a single narrow
      band, leaving the adjacent band (the real QTY band) with no header word.
      Two recovery rules prevent silent data corruption:

      Rule A — Split merged "ITEM QTY" header at midpoint.
        Creates separate ITEM and QTY band entries, then extends the following
        band leftward so description data that physically starts in the old QTY
        zone is captured correctly.

      Rule B — Infer "QTY" for a narrow orphan band following an ITEM column.
        Covers the case where the merged text is not recognised by Rule A but
        the orphan (< 120pt) immediately follows the ITEM band.

    Bands with no header word that do NOT match Rule B are still skipped
    (e.g. row-number gutters).

    The final column's right band extends 1000pt to the right.
    """
    if len(dividers) < 2:
        return []
    columns = []
    _ORPHAN_QTY_MAX_WIDTH = 120  # pt — narrower than this after ITEM → QTY

    for i in range(len(dividers) - 1):
        x0, x1 = dividers[i], dividers[i + 1]
        band_words = [w for w in header_row_words
                      if x0 <= (w[0] + w[2]) / 2 <= x1]

        if not band_words:
            # Rule B: narrow orphan immediately after an ITEM column → infer QTY.
            if (columns
                    and "ITEM" in columns[-1]["name"].upper()
                    and (x1 - x0) < _ORPHAN_QTY_MAX_WIDTH):
                columns.append({"name": "QTY", "x0": x0, "x1": x1,
                                "band_x0": x0, "band_x1": x1})
            # else: wider orphan — genuine gutter, skip silently
            continue

        name = " ".join(w[4].strip() for w in sorted(band_words, key=lambda w: w[0]))

        # Rule A: "ITEM QTY" merged header — split at midpoint.
        name_up = name.upper().strip()
        if "ITEM" in name_up and ("QTY" in name_up or "QUANTITY" in name_up):
            mid = (x0 + x1) / 2
            columns.append({"name": "ITEM", "x0": x0, "x1": mid,
                            "band_x0": x0, "band_x1": mid})
            # QTY right edge will serve as the description band's left edge;
            # extend description band leftward when it is added (handled below
            # via band_x0 extension on the next column).
            columns.append({"name": "QTY", "x0": mid, "x1": x1,
                            "band_x0": mid, "band_x1": x1})
            continue

        col_entry = {"name": name, "x0": x0, "x1": x1,
                     "band_x0": x0, "band_x1": x1}

        # If the previous column is a QTY band that was split from a merged
        # header, extend this column's band_x0 leftward to the QTY band's x0
        # so that description data physically starting in the old merged zone
        # is captured here rather than lost.
        if (columns
                and columns[-1]["name"].upper() == "QTY"
                and "DESC" in name_up):
            col_entry["band_x0"] = columns[-1]["x0"]

        columns.append(col_entry)

    # Catch any header words to the right of the last divider
    last_x = dividers[-1]
    tail = [w for w in header_row_words if (w[0] + w[2]) / 2 > last_x]
    if tail:
        name = " ".join(w[4].strip() for w in sorted(tail, key=lambda w: w[0]))
        columns.append({"name": name, "x0": last_x, "x1": last_x + 1000,
                        "band_x0": last_x, "band_x1": last_x + 1000})
    return columns


def assign_word_to_col(word, columns):
    # Use the word's LEFT EDGE (x0) to decide which column it belongs to.
    # Using the centre caused description words that start inside the description
    # band but extend past the right divider to be assigned to the spec column —
    # e.g. "FEED" at x=[1890, 1950] has centre 1920 (inside spec band) even
    # though the word clearly starts in the description column at x=1890.
    # Left-edge assignment matches how Inventor lays out left-aligned BOM text.
    x0 = word[0]
    for i, col in enumerate(columns):
        if col["band_x0"] <= x0 < col["band_x1"]:
            return i
    return None


# ============================================================
#  COLUMN MAPPING — dynamic PDF columns → fixed output columns
# ============================================================

def map_source_columns(col_names):
    """
    Map extracted PDF column names to standard output column indices.
    Returns dict: {output_col_name: source_index_or_None}
    """
    def find(keys):
        for i, name in enumerate(col_names):
            n = name.upper().strip()
            for k in keys:
                if k in n:
                    return i
        return None

    return {
        "Item":          find(["ITEM"]),
        "QTY":           find(["QTY", "QUANTITY"]),
        "Description":   find(["DESCRIPTION", "DESC"]),
        "Specification": find(["SPECIFICATION", "SPEC", "PART"]),
    }


# ============================================================
#  DATA ROW EXTRACTION
# ============================================================

def item_sort_key(text):
    m = ITEM_FULL_RE.match(str(text).strip())
    if not m:
        return (9999, "")
    return (int(m.group(1)), m.group(2).lower())


def extract_row_cells(words, item_word, columns):
    row_y = _wcy(item_word)
    row_words = [w for w in words if abs(_wcy(w) - row_y) <= DATA_ROW_Y_TOLERANCE_PT]
    row_words.sort(key=lambda w: w[0])

    cell_parts = {i: [] for i in range(len(columns))}
    for w in row_words:
        col_idx = assign_word_to_col(w, columns)
        if col_idx is not None:
            cell_parts[col_idx].append(w[4].strip())

    return [" ".join(cell_parts[i]).strip() for i in range(len(columns))]


# ============================================================
#  PER-PDF EXTRACTION
# ============================================================

def extract_bom_from_pdf(pdf_path):
    """
    Extract BOM data from a single PDF.
    Returns dict {drawing, col_map, rows} or None.
    rows is list of {item_text, cells[]}.
    """
    drawing = Path(pdf_path).stem
    print(f"  {drawing}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"    ERROR opening: {e}")
        return None

    col_map   = None
    all_rows  = []
    raw_cols  = []
    used_ocr  = False   # set True if any page needed Tesseract fallback

    for page_num, page in enumerate(doc):
        words, ocr_used = get_page_words(page)
        if not words:
            if _TESSERACT_EXE:
                print(f"    Page {page_num + 1}: no text (native or OCR) — skipped")
            else:
                print(f"    Page {page_num + 1}: no extractable text — skipped (SHX/rasterised?)")
            continue
        if ocr_used:
            used_ocr = True
            print(f"    Page {page_num + 1}: OCR fallback — {len(words)} words found")

        headers = find_bom_headers(words)
        if not headers:
            # ── AutoCAD inverted-BOM fallback (OCR pages only) ────────────────
            # AutoCAD SHX drawings use OCR.  The ITEM/QTY column cells are too
            # narrow for OCR to capture their header text reliably, so
            # find_bom_headers() returns empty.  Instead we anchor on the wider
            # DESCRIPTION + PART header cells and extract rows above the header.
            if not ocr_used:
                continue
            pw_p, ph_p = page.rect.width, page.rect.height
            hinfo = find_bom_header_autocad(words, pw_p, ph_p)
            if not hinfo:
                continue
            acad_rows = extract_inverted_bom_rows(words, hinfo)
            if not acad_rows:
                print(f"    Page {page_num + 1}: AutoCAD header detected — no rows extracted")
                continue
            print(f"    Page {page_num + 1}: AutoCAD inverted BOM — {len(acad_rows)} item(s)")
            for r in acad_rows:
                desc_s = r["cells"][2][:45]
                spec_s = r["cells"][3][:30]
                print(f"      [{r['item_text']:>4s}] y={r['item_y']:6.1f}"
                      f"  desc={desc_s!r}  spec={spec_s!r}")
            if col_map is None:
                raw_cols = ["ITEM", "QTY", "DESCRIPTION", "SPECIFICATION"]
                col_map  = {"Item": 0, "QTY": 1, "Description": 2, "Specification": 3}
                print(f"    Columns detected : {raw_cols}  [AutoCAD inverted BOM]")
                print(f"    Column mapping   : {col_map}")
            all_rows.append(acad_rows)
            continue   # done with this page — skip normal Inventor path
            # ─────────────────────────────────────────────────────────────────

        # Deduplicate headers within HEADER_ROW_TOLERANCE_PT of each other.
        # Integer round() was too tight — two detections on the same row
        # could differ by a fraction of a pt and slip through.
        deduped_headers = []
        seen_ys: list = []
        for hw in headers:
            y = _wcy(hw)
            if not any(abs(y - sy) <= HEADER_ROW_TOLERANCE_PT for sy in seen_ys):
                seen_ys.append(y)
                deduped_headers.append(hw)
        headers = deduped_headers

        # Sort headers top-to-bottom so we can compute y-ceilings correctly.
        headers.sort(key=lambda hw: _wcy(hw))

        for h_idx, header_word in enumerate(headers):
            hrow    = get_header_row_words(words, header_word)

            # Try authoritative vector-line column detection first.
            # Inventor BOMs are always drawn as ruled tables, so the PDF contains
            # exact vertical column dividers as vector paths.  If we find ≥3
            # dividers the bands are exact and we skip the header-word heuristic.
            dividers = get_bom_column_dividers(page, _wcy(header_word), hrow=hrow)
            if dividers and len(dividers) >= 3:
                columns = build_columns_from_dividers(dividers, hrow)
                col_method = f"vector ({len(dividers)} dividers)"
            else:
                columns = cluster_into_columns(hrow)
                col_method = "header-word heuristic"

            if not columns:
                continue

            if col_map is None:
                raw_cols = [c["name"] for c in columns]
                col_map  = map_source_columns(raw_cols)
                print(f"    Columns detected : {raw_cols}")
                print(f"    Column method    : {col_method}")
                print(f"    Column mapping   : {col_map}")
                for c in columns:
                    print(f"      {c['name']!r:30s}  x=[{c['x0']:.1f},{c['x1']:.1f}]  "
                          f"band=[{c['band_x0']:.1f},{c['band_x1']:.1f}]")
                # ── Corruption guard ──────────────────────────────────────────
                # If Item and QTY map to the same source column the extraction
                # would silently mix item numbers, quantities and description
                # words into one cell (e.g. qty='5 12 M20').  Hard-stop here;
                # a blank row in Excel is safer than a corrupt row.
                if (col_map.get("Item") is not None
                        and col_map.get("Item") == col_map.get("QTY")):
                    print(f"    ERROR: Item and QTY both map to column "
                          f"{col_map['Item']} — data would be corrupt. "
                          f"Skipping drawing to prevent corrupt output.")
                    print(f"    HINT: Check whether the header row uses a "
                          f"merged 'ITEM QTY' cell. build_columns_from_dividers "
                          f"should have split it — review divider positions above.")
                    return None
                # ─────────────────────────────────────────────────────────────

            # When multiple BOM tables share a page, cap item collection at the
            # next header's y so items from table N don't bleed into table N+1.
            next_header_y = _wcy(headers[h_idx + 1]) if h_idx + 1 < len(headers) else None

            item_col_words = extract_item_column(words, header_word, max_y=next_header_y)
            inverted_native = False
            if not item_col_words:
                # Inverted BOM? Try looking ABOVE the header (AutoCAD convention
                # even when the PDF has a native text layer, e.g. drawing 000160).
                item_col_words = extract_item_column(words, header_word, above=True)
                if not item_col_words:
                    print(f"    Page {page_num + 1}: header found, no item numbers — skipped")
                    continue
                inverted_native = True
                print(f"    Page {page_num + 1}: inverted BOM (items above header)")

            print(f"    Page {page_num + 1}: {len(item_col_words)} item(s)")

            group_rows = []
            for iw in item_col_words:
                cells = extract_row_cells(words, iw, columns)
                group_rows.append({"item_text": iw[4].strip(), "item_y": iw[1], "cells": cells})
                # Diagnostic: one line per item so the log shows exactly what was extracted
                item_txt = iw[4].strip()
                qty_txt  = cells[col_map["QTY"]]       if col_map and "QTY"         in col_map else ""
                desc_txt = cells[col_map["Description"]] if col_map and "Description" in col_map else ""
                spec_idx = col_map.get("Specification") if col_map else None
                spec_txt = cells[spec_idx] if (spec_idx is not None and isinstance(spec_idx, int) and spec_idx < len(cells)) else ""
                print(f"      [{item_txt:>4s}] y={iw[1]:6.1f}  qty={qty_txt!r:5}  "
                      f"desc={desc_txt[:45]!r}  spec={spec_txt[:30]!r}")

            # ── Continuation-line sweep ──────────────────────────────────────
            # Inventor BOM cells can wrap to a second physical line.
            # extract_row_cells only captures words within DATA_ROW_Y_TOLERANCE_PT
            # of the item's y-coord; continuation words (~14pt below) are missed.
            #
            # Sweep all page words in desc/spec columns that are NOT on any
            # item's y-row; group them by y-proximity, then merge each orphan
            # group into the item whose y is nearest above it.
            _MAX_CONT_GAP = 40.0   # cap: ~2.5× a typical 16pt row spacing
            # Shadow-text guard: AutoCAD PDFs render each row's text twice, with
            # the duplicate ~6pt below the main row (outside DATA_ROW_Y_TOLERANCE_PT
            # so it escapes extract_row_cells, but is NOT a real second line).
            # Real continuation lines appear at ~23pt.  A minimum gap of 12pt
            # separates duplicates (≤6.5pt) from genuine continuations (≥22pt).
            _MIN_CONT_DY = 12.0
            # Header-ceiling guard: for an inverted BOM the header row sits just
            # below item 1.  Exclude any orphan words at or below the header's y
            # so the header text ("DESCRIPTION PART No. / SPECIFICATION …") is
            # never appended to item 1's cells.
            _bom_ceiling_y = (_wcy(header_word)
                              if inverted_native else float("inf"))
            if group_rows and columns and col_map:
                _spec_ci = col_map.get("Specification")
                _desc_ci = col_map.get("Description")
                _item_ys = [r["item_y"] for r in group_rows]

                # Collect words NOT owned by any item row.
                # Accept desc/spec column words normally.
                # Also accept words that fall in the item/qty bands — on a
                # continuation row these are description overflow (e.g. "TYPE"
                # wrapping from the description column into the QTY band).
                # Words with no column assignment (_ci is None) are skipped.
                _orphan: list = []
                for _w in words:
                    _wy = _wcy(_w)
                    if any(abs(_wy - _iy) <= DATA_ROW_Y_TOLERANCE_PT
                           for _iy in _item_ys):
                        continue   # belongs to an existing item row
                    if _wy >= _bom_ceiling_y:
                        continue   # at or below the BOM header row — exclude
                    _ci = assign_word_to_col(_w, columns)
                    if _ci is None:
                        continue
                    # Accept all assigned columns — item/qty-band words on
                    # continuation rows are handled as desc overflow in the
                    # append loop below.
                    _orphan.append((_wy, _w[0], _w, _ci))

                # Group orphan words into continuation rows by y-proximity.
                _orphan.sort(key=lambda t: (t[0], t[1]))
                _cont_rows: list = []
                for _wy, _x0, _w, _ci in _orphan:
                    if (_cont_rows
                            and abs(_wy - _cont_rows[-1][0])
                            <= DATA_ROW_Y_TOLERANCE_PT):
                        _cont_rows[-1][1].append((_w, _ci))
                    else:
                        _cont_rows.append([_wy, [(_w, _ci)]])

                for _wy_r, _wlist in _cont_rows:
                    # Find nearest item ABOVE this orphan row (positive dy).
                    _par, _mdy = None, float("inf")
                    for _r in group_rows:
                        _dy = _wy_r - _r["item_y"]
                        if 0 < _dy < _mdy:
                            _mdy, _par = _dy, _r
                    if _par is None or _mdy > _MAX_CONT_GAP:
                        continue
                    if _mdy < _MIN_CONT_DY:
                        continue   # shadow-text duplicate — too close to be a real second line
                    # Ensure no other item row sits between parent and orphan.
                    if any(0 < _r["item_y"] - _par["item_y"] < _mdy
                           for _r in group_rows if _r is not _par):
                        continue
                    # Strip any trailing mass value from the parent spec NOW,
                    # before appending continuation text, so the mass-strip that
                    # runs later still sees it at the end of the spec string.
                    # (Same regex as the post-processing mass strip at line ~2576.)
                    # Strip trailing mass value before appending continuation so
                    # the post-processing mass strip (anchored at end) still fires.
                    if (_spec_ci is not None and isinstance(_spec_ci, int)
                            and _spec_ci < len(_par["cells"])):
                        _spec_before = _par["cells"][_spec_ci]
                        _par["cells"][_spec_ci] = re.sub(
                            r'\s+\d[\d.,]*\s*(?:k(?:g)?|lbs?|lb)?\s*$',
                            '', _par["cells"][_spec_ci],
                            flags=re.IGNORECASE).strip()
                        print(f"      [cont-sweep] item {_par['item_text']!r}"
                              f"  pre-strip: {_spec_before!r} → {_par['cells'][_spec_ci]!r}")
                    # Guard: if the orphan text assembles to a BOM column-header
                    # row (e.g. "DESCRIPTION PART No. / SPECIFICATION"), skip it.
                    # This prevents header text that sits just below the last item
                    # (inverted or bottom-header BOMs) from polluting that item's spec.
                    _orphan_text = " ".join(_w[4].strip() for _w, _ in _wlist)
                    if re.search(
                            r'\b(ITEM|QTY|QUANTITY)\b.*\bDESCRIPTION\b'
                            r'|\bDESCRIPTION\b.*\b(SPECIFICATION|PART\s*N[Oo])',
                            _orphan_text, re.IGNORECASE):
                        continue
                    # Append words (left→right) to parent's cells.
                    # Continuation rows never carry real item numbers or quantities,
                    # so any word that falls in the item/qty band is description
                    # overflow and should be appended to desc rather than dropped.
                    _wlist.sort(key=lambda t: t[0][0])
                    for _w, _ci in _wlist:
                        _wt = _w[4].strip()
                        if _ci == _spec_ci:
                            _par["cells"][_spec_ci] = (
                                _par["cells"][_spec_ci] + " " + _wt).strip()
                        elif _ci == _desc_ci or (
                                _desc_ci is not None and _ci not in (_spec_ci,)):
                            # Words that land in item/qty bands on a continuation
                            # row are description overflow — append to desc.
                            _par["cells"][_desc_ci] = (
                                _par["cells"][_desc_ci] + " " + _wt).strip()
                    _txt = " ".join(_w[4].strip() for _w, _ in _wlist)
                    _spec_final = (
                        _par["cells"][_spec_ci]
                        if (_spec_ci is not None and isinstance(_spec_ci, int)
                            and _spec_ci < len(_par["cells"]))
                        else ""
                    )
                    _desc_final = (
                        _par["cells"][_desc_ci]
                        if (_desc_ci is not None and isinstance(_desc_ci, int)
                            and _desc_ci < len(_par["cells"]))
                        else ""
                    )
                    print(f"      [cont-sweep] item {_par['item_text']!r}"
                          f"  dy={_mdy:.1f}pt  +{_txt!r}"
                          f"  → final desc={_desc_final!r}"
                          f"  final spec={_spec_final!r}")

            all_rows.append(group_rows)   # one sub-list per BOM table

    # ── Title block: REV + description ───────────────────────────────────
    title_rev, title_desc = extract_title_block_info(doc)
    if title_rev:
        print(f"    Title block rev  : {title_rev!r}")
    if title_desc:
        print(f"    Title block desc : {title_desc!r}")

    doc.close()

    if not all_rows:
        print("    No BOM data extracted.")
        return None

    # Deduplicate within each BOM group (keep first occurrence per item number).
    bom_groups = []
    for group in all_rows:
        seen_g: set = set()
        deduped_g = []
        for row in group:
            if row["item_text"] not in seen_g:
                seen_g.add(row["item_text"])
                deduped_g.append(row)
        deduped_g.sort(key=lambda r: item_sort_key(r["item_text"]))
        if deduped_g:
            bom_groups.append(deduped_g)

    return {"drawing": drawing, "col_map": col_map or {}, "raw_cols": raw_cols,
            "bom_groups": bom_groups,
            "title_rev": title_rev, "title_desc": title_desc,
            "used_ocr": used_ocr}


# ============================================================
#  IDW/DWG EXTRACTION  (Inventor COM — reads PartsLists directly)
# ============================================================

# Shared Inventor instance — kept alive across drawings in the same run
# so we don't pay the startup cost more than once.
_INV_APP = None
_INV_STARTED_HERE = False


def _get_inventor():
    """
    Attach to a running Inventor instance or launch a hidden one.
    Sets SilentOperation=True to suppress all dialogs.
    Returns (inv_app, launched_by_us).
    """
    global _INV_APP, _INV_STARTED_HERE
    if _INV_APP is not None:
        return _INV_APP, _INV_STARTED_HERE
    try:
        import win32com.client as _w32
        import pywintypes as _pwt
    except ImportError:
        raise RuntimeError("pywin32 is required for Inventor COM extraction.\n"
                           "Run:  pip install pywin32")
    try:
        app = _w32.GetActiveObject("Inventor.Application")
        launched = False
        print("    Attached to running Inventor instance.")
    except Exception:
        app = _w32.Dispatch("Inventor.Application")
        app.Visible = False
        launched = True
        print("    Launched new Inventor instance (hidden).")
    app.SilentOperation = True
    _INV_APP = app
    _INV_STARTED_HERE = launched
    return app, launched


def _quit_inventor_if_ours():
    """Shut down the Inventor instance only if WE started it."""
    global _INV_APP, _INV_STARTED_HERE
    if _INV_APP is not None and _INV_STARTED_HERE:
        try:
            _INV_APP.SilentOperation = False
            _INV_APP.Quit()
            print("    Inventor closed.")
        except Exception:
            pass
    _INV_APP = None
    _INV_STARTED_HERE = False


def _inv_custom_prop(doc, name: str) -> str:
    """Read an iProperty by *name* from any property set on *doc*.

    Uses index-based COM iteration (more reliable than for-in enumeration
    on Inventor PropertySets) and returns the first non-empty value found.
    """
    try:
        n = doc.PropertySets.Count
    except Exception:
        return ""
    for i in range(1, n + 1):
        try:
            ps = doc.PropertySets.Item(i)
        except Exception:
            continue
        try:
            val = str(ps.Item(name).Value).strip()
            if val:
                return val
        except Exception:
            pass
    return ""


def _inv_get_rev(draw_doc) -> str:
    # Diagnostic: log all PropertySet names so we can see what's available
    try:
        ps_names = [draw_doc.PropertySets.Item(i).Name
                    for i in range(1, draw_doc.PropertySets.Count + 1)]
        print(f"    [inv-rev] PropertySets ({len(ps_names)}): {ps_names}")
    except Exception as _e:
        print(f"    [inv-rev] PropertySets: (error listing — {_e})")

    # Inventor's "Design Tracking Properties" set carries a standard property
    # "Revision Number" that defaults to '-' (hyphen) when never filled in.
    # That default is truthy so it would short-circuit the search before we
    # reach the real custom "REVISION" property.  Skip known placeholder values.
    _DEFAULTS = {"-", "--", "0", "00", "000"}

    # Try custom property names FIRST so the real value is found before the
    # standard "Revision Number" default ('-') can intercept.
    for prop_name in ("REVISION", "REV", "Revision Number", "Revision"):
        val = _inv_custom_prop(draw_doc, prop_name)
        if val and val not in _DEFAULTS:
            print(f"    [inv-rev] found {prop_name!r} = {val!r}")
            return val.strip()
        else:
            reason = f"{val!r} (default placeholder)" if val in _DEFAULTS else "not found or empty"
            print(f"    [inv-rev] {prop_name!r} — {reason}")
    return ""


def _inv_find_col(parts_list, *keys) -> int:
    try:
        for i in range(1, parts_list.PartsListColumns.Count + 1):
            title = parts_list.PartsListColumns.Item(i).Title.upper()
            if any(k in title for k in keys):
                return i
    except Exception:
        pass
    return 0


def _inv_cell_val(row, col: int) -> str:
    if col <= 0:
        return ""
    try:
        return str(row.Item(col).Value)
    except Exception:
        return ""


def _inv_item_number(text: str) -> int:
    """Leading-digit sort key — "5a" → 5, "" → 9999."""
    digits = ""
    for ch in text:
        if ch.isdigit():
            digits += ch
        else:
            break
    return int(digits) if digits else 9999


def _inv_read_parts_list(parts_list) -> list:
    """
    Read one Inventor PartsLists into a list of (item, qty, desc, spec) tuples,
    sorted by item number ascending.
    """
    item_col = _inv_find_col(parts_list, "ITEM")
    qty_col  = _inv_find_col(parts_list, "QTY", "QUANTITY")
    desc_col = _inv_find_col(parts_list, "DESCRIPTION", "DESC")
    spec_col = _inv_find_col(parts_list, "PART", "SPECIFICATION", "SPEC")

    print(f"      Cols: ITEM={item_col} QTY={qty_col} DESC={desc_col} SPEC={spec_col}")
    if item_col == 0 or desc_col == 0:
        print("      Cannot find ITEM or DESCRIPTION column — skipping")
        return []

    rows = []
    try:
        for row in parts_list.PartsListRows:
            try:
                if not row.Visible:
                    continue
            except Exception:
                pass
            item    = _inv_cell_val(row, item_col)
            qty     = _inv_cell_val(row, qty_col)
            desc    = _inv_cell_val(row, desc_col)
            spec    = _inv_cell_val(row, spec_col)
            if not item and not desc:
                continue
            rows.append((item, qty, desc, spec))
    except Exception as e:
        print(f"      WARNING reading rows: {e}")
        return []

    rows.sort(key=lambda r: _inv_item_number(r[0]))
    return rows


def extract_bom_from_inventor(idw_path):
    """
    Extract BOM data from an Inventor IDW (or Inventor-format DWG) via COM.
    Returns the same result dict shape as extract_bom_from_pdf / extract_bom_from_dwg,
    or None when no BOM is found.
    """
    drawing = Path(idw_path).stem
    print(f"  {drawing}  [IDW — Inventor COM]")

    try:
        inv, _ = _get_inventor()
    except Exception as e:
        print(f"    ERROR connecting to Inventor: {e}")
        return None

    draw_doc = None
    opened_here = False
    try:
        # Re-use if already open
        for i in range(1, inv.Documents.Count + 1):
            try:
                d = inv.Documents.Item(i)
                if d.FullFileName.lower() == str(idw_path).lower():
                    draw_doc = d
                    print("    Already open in Inventor — reusing.")
                    break
            except Exception:
                pass

        if draw_doc is None:
            print(f"    Opening: {idw_path}")
            # Open with FileOpenOptions to force read-only and suppress all
            # interactive prompts (vault check-out, "file in use", etc.)
            try:
                open_opts = inv.TransientObjects.CreateFileOpenOptions()
                open_opts.CheckOutFromVault   = False   # don't prompt to check out
                open_opts.ReferenceCheckPolicy = 68     # kSkipUnavailableReferences
                open_opts.OpenFileDescriptors  = False  # suppress descriptor prompts
                draw_doc = inv.Documents.OpenWithOptions(str(idw_path), open_opts, False)
            except Exception:
                # Fallback: plain open, read-only flag via property after open
                draw_doc = inv.Documents.Open(str(idw_path), False)
            opened_here = True
            try:
                draw_doc.DeferUpdates = True
                print("    Opened OK (express/draft mode)")
            except Exception:
                print("    Opened OK")

        rev       = _inv_get_rev(draw_doc) or ""
        equip     = _inv_custom_prop(draw_doc, "4EQUIPMENT")
        draw_type = _inv_custom_prop(draw_doc, "5DRAWING TYPE")
        if equip:     print(f"    Equipment  : {equip}")
        if draw_type: print(f"    DrawingType: {draw_type}")

        # Collect PartsLists from all sheets
        parts_lists = []
        try:
            for sheet in draw_doc.Sheets:
                for pl in sheet.PartsLists:
                    try:
                        box = pl.RangeBox
                        if box.MaxPoint.X > 0:
                            parts_lists.append(pl)
                    except Exception:
                        parts_lists.append(pl)
        except Exception as e:
            print(f"    WARNING collecting PartsLists: {e}")

        print(f"    PartsLists found: {len(parts_lists)}")
        if not parts_lists:
            print("    No PartsLists on any sheet.")
            return None

        bom_groups = []
        col_map = {"Item": 0, "QTY": 1, "Description": 2, "Specification": 3}

        for pl_idx, pl in enumerate(parts_lists, start=1):
            raw_rows = _inv_read_parts_list(pl)
            print(f"    PartsLists[{pl_idx}]: {len(raw_rows)} row(s)")
            if not raw_rows:
                continue

            group = []
            for item, qty, desc, spec in raw_rows:
                print(f"      [{item:>4s}]  qty={qty!r:5}  desc={desc[:45]!r}  spec={spec[:30]!r}")
                group.append({
                    "item_text": item,
                    "item_y":    0.0,
                    "cells":     [item, qty, desc, spec],
                })
            bom_groups.append(group)

        if not bom_groups:
            return None

        # Build title_desc from equipment + drawing type (mirrors iLogic convention)
        parts = [p for p in [equip, draw_type] if p]
        title_desc = " - ".join(parts) if parts else ""

        return {
            "drawing":    drawing,
            "col_map":    col_map,
            "raw_cols":   ["ITEM", "QTY", "DESCRIPTION", "SPECIFICATION"],
            "bom_groups": bom_groups,
            "title_rev":  rev,
            "title_desc": title_desc,
            "used_ocr":   False,
        }

    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback as _tb
        print(_tb.format_exc())
        return None

    finally:
        if draw_doc is not None and opened_here:
            try:
                draw_doc.Close(SkipDocumentSave=True)
                print("    Closed drawing.")
            except Exception:
                pass


# ============================================================
#  DWG EXTRACTION  (AutoCAD COM — direct attribute read, no OCR)
# ============================================================

def extract_bom_from_dwg(dwg_path, acad=None):
    """
    Extract BOM data directly from an AutoCAD .dwg file via COM automation.

    Requires AutoCAD to be installed and accessible via COM.
    No OCR — reads attribute values directly from block inserts in paper space.

    BOM block   : 'XT Item Description Line'
    Attributes  : ITEM, QTY, DESCRIPTION, JC-000000 (spec/part no.), NOTE (mass)
    Title block : 'A1 XSTRATA'  →  REVISION, DRAWING_DESCRIPTION_1, DRAWING_DESCRIPTION_2

    acad: optional pre-connected AutoCAD COM instance.  When None, a connection
          is established internally (legacy / single-file call behaviour).

    Returns the same dict format as extract_bom_from_pdf(), or None on failure.
    """
    import time as _time

    drawing = Path(dwg_path).stem
    print(f"  {drawing}  [DWG — AutoCAD COM]")

    _acad_local = False   # did WE create the acad instance in this call?
    if acad is None:
        try:
            import win32com.client
        except ImportError:
            print("    ERROR: pywin32 not installed — cannot read DWG via COM.")
            print("    Install: pip install pywin32")
            return None
        try:
            print("    Connecting to AutoCAD...")
            acad = win32com.client.Dispatch("AutoCAD.Application")
            try:
                acad.Visible = False
            except Exception:
                pass
            print(f"    AutoCAD: {acad.Version}")
            _acad_local = True
        except Exception as e:
            print(f"    ERROR: AutoCAD COM connection failed — {e}")
            return None

    doc = None
    # ── Check if the file is already open in AutoCAD ──────────────────────────
    # Use os.path.normcase + abspath so drive-letter case and slash direction
    # don't cause a false miss (common with Vault paths).
    import os as _os
    _target_norm = _os.path.normcase(_os.path.abspath(str(dwg_path)))
    try:
        for _i in range(acad.Documents.Count):
            _existing = acad.Documents.Item(_i)
            try:
                _ex_norm = _os.path.normcase(_os.path.abspath(_existing.FullName))
                if _ex_norm == _target_norm:
                    doc = _existing
                    print(f"    (already open in AutoCAD — reusing document)")
                    break
            except Exception:
                continue
    except Exception:
        pass

    # ── Open the file if not already open ────────────────────────────────────
    _tmp_dir = None   # track any temp copy so we can clean up
    if doc is None:
        # First attempt: open direct (works for non-Vault files)
        _direct_ok = False
        def _open_with_retry(path, label=""):
            """Open a DWG in AutoCAD, retrying on RPC_E_CALL_REJECTED (busy)."""
            for _r in range(12):
                try:
                    return acad.Documents.Open(str(path), True)
                except Exception as _e:
                    _es = str(_e)
                    if '-2147418111' in _es or 'rejected' in _es.lower() or 'busy' in _es.lower():
                        if _r == 0:
                            print(f"    {label}AutoCAD busy — waiting...")
                        _time.sleep(2.0)
                        continue
                    raise
            raise RuntimeError(f"AutoCAD still busy after 12 retries{' (' + label.strip() + ')' if label else ''}")

        print(f"    Opening: {dwg_path}")
        try:
            doc = _open_with_retry(dwg_path)
            _direct_ok = True
        except Exception as _e_direct:
            # Direct open failed — log what files AutoCAD currently has open
            # so we can diagnose any path-mismatch in the "already open" check.
            try:
                _open_names = []
                for _di in range(acad.Documents.Count):
                    try:
                        _open_names.append(acad.Documents.Item(_di).FullName)
                    except Exception:
                        pass
                if _open_names:
                    print(f"    [AutoCAD docs open: {_open_names}]")
                else:
                    print(f"    [AutoCAD has no docs open]")
            except Exception:
                pass
            print(f"    Direct open failed ({_e_direct}) — trying temp-copy fallback")

        if not _direct_ok and doc is None:
            # Fallback: copy DWG to a temp folder outside C:\Vault\ so AutoCAD
            # COM can open it without Vault interception.  Block attributes are
            # embedded in the DWG itself so no Vault context is needed.
            import shutil as _shutil, tempfile as _tempfile
            try:
                _tmp_dir = _tempfile.mkdtemp(prefix="bom_acad_")
                _tmp_path = _os.path.join(_tmp_dir, _os.path.basename(str(dwg_path)))
                _shutil.copy2(str(dwg_path), _tmp_path)
                print(f"    Opening temp copy: {_tmp_path}")
                doc = _open_with_retry(_tmp_path, label="temp copy — ")
            except Exception as _e_tmp:
                print(f"    ERROR: temp-copy open also failed — {_e_tmp}")
                if _tmp_dir:
                    try:
                        _shutil.rmtree(_tmp_dir)
                    except Exception:
                        pass
                return None

        # Wait for AutoCAD to finish loading (it returns before drawing is ready)
        if doc is not None:
            for _attempt in range(30):
                try:
                    _ = doc.Layouts.Count
                    break
                except Exception:
                    _time.sleep(1.0)

    try:
        _result = _read_dwg_bom(doc, drawing)
    except Exception as e:
        print(f"    ERROR reading DWG BOM: {e}")
        print("    " + traceback.format_exc().replace("\n", "\n    "))
        _result = None

    # Close and delete temp copy if we made one
    if _tmp_dir is not None:
        import shutil as _shutil
        try:
            doc.Close(False)
        except Exception:
            pass
        try:
            _shutil.rmtree(_tmp_dir)
        except Exception:
            pass

    return _result


def _connect_autocad():
    """
    Connect to a running AutoCAD instance, or launch one if none is running.

    Always uses Dispatch() — GetActiveObject() can return a COM proxy that
    refuses Documents.Open() when the user's AutoCAD session is active.
    Dispatch() routes through the COM registration and returns a usable proxy
    regardless of whether AutoCAD was already running.

    We determine "launched_here" by checking whether AutoCAD had any open
    documents before we connected:
      - 0 documents → we just launched it (or it's a fresh, empty session)
      - ≥1 documents → it was already in use; leave it open when done

    Returns (acad, launched_here).
    """
    try:
        import win32com.client
        import time as _time
    except ImportError:
        return None, False

    # ── Prefer the running instance; only launch fresh if none is running ─────
    _launched = False
    acad = None
    try:
        acad = win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception:
        # AutoCAD not running — launch it.
        try:
            acad = win32com.client.Dispatch("AutoCAD.Application")
            _launched = True
        except Exception as e:
            print(f"  ERROR: cannot connect to AutoCAD — {e}")
            return None, False

    # Wait for AutoCAD to be ready (handles RPC_E_CALL_REJECTED on busy app).
    _ver = ""
    for _ in range(30):
        try:
            _ver = acad.Version
            break
        except Exception:
            _time.sleep(1.0)

    if _launched:
        try:
            acad.Visible = False
        except Exception:
            pass
        print(f"  [AutoCAD launched{(' — v' + _ver) if _ver else ''}]")
    else:
        print(f"  [AutoCAD already open — reusing instance{(' v' + _ver) if _ver else ''}]")

    return acad, _launched


def _dwg_item_number(text: str) -> tuple:
    """
    Return a sort key for a BOM item label so rows come out in ascending order.

    Examples:  "1" → (1, "")   "5a" → (5, "a")   "5b" → (5, "b")
               "10" → (10, "")   "" → (9999, "")

    The tuple (int_part, suffix) sorts sub-items (5a, 5b) after their parent
    row (5) and before the next integer (6), matching the visual BOM order.
    """
    text = text.strip()
    digits = ""
    for ch in text:
        if ch.isdigit():
            digits += ch
        else:
            break
    suffix = text[len(digits):]
    return (int(digits) if digits else 9999, suffix)


def _read_dwg_bom(doc, drawing):
    """
    Inner worker — doc is already open.  Iterates all paper space layouts,
    collects 'XT Item Description Line' attribute blocks (BOM rows) and
    the 'A1 XSTRATA' title block.

    Returns the result dict, or None when no BOM rows are found.
    """
    bom_rows   = []   # list of (y_coord, attrs_dict)
    title_rev  = ""
    title_desc = ""

    # ── Iterate layouts, skip Model ───────────────────────────────────────────
    try:
        layouts   = doc.Layouts
        n_layouts = layouts.Count
    except Exception as e:
        print(f"    ERROR: cannot get layouts — {e}")
        return None

    print(f"    Layouts: {n_layouts}")
    original_layout_name = ""
    try:
        original_layout_name = doc.ActiveLayout.Name
    except Exception:
        pass

    for i in range(n_layouts):
        try:
            layout = layouts.Item(i)
            lname  = layout.Name
        except Exception:
            continue

        if lname.lower() == "model":
            continue

        # Activate layout so doc.PaperSpace points at the right collection.
        try:
            doc.ActiveLayout = layout
            ps = doc.PaperSpace
        except Exception as e:
            print(f"    Layout {lname!r}: cannot activate — {e}")
            continue

        ps_count = 0
        try:
            ps_count = ps.Count
        except Exception:
            pass

        bom_found_here = 0
        seen_block_names = set()          # for diagnostics when no BOM found
        for j in range(ps_count):
            try:
                ent = ps.Item(j)
            except Exception:
                continue

            try:
                if ent.ObjectName != "AcDbBlockReference":
                    continue
            except Exception:
                continue

            try:
                ename = ent.EffectiveName
            except Exception:
                continue

            seen_block_names.add(ename)

            ename_upper = ename.upper()

            # ── BOM row block ─────────────────────────────────────────────────
            # Case-insensitive match on "XT ITEM" to handle variations like
            # "XT Item Description Line", "XT ITEM DESCRIPTION LINE", etc.
            if "XT ITEM" in ename_upper:
                attrs = {}
                try:
                    if ent.HasAttributes:
                        for a in ent.GetAttributes():
                            attrs[a.TagString] = a.TextString
                except Exception:
                    pass
                try:
                    ins = ent.InsertionPoint
                    y   = ins[1]
                except Exception:
                    y = 0.0
                bom_rows.append((y, attrs))
                bom_found_here += 1

            # ── Title block — primary (named match) ───────────────────────────
            elif ename_upper in ("A1 XSTRATA", "A1XSTRATA") and not title_rev:
                try:
                    if ent.HasAttributes:
                        tb     = {a.TagString: a.TextString for a in ent.GetAttributes()}
                        title_rev = tb.get("REVISION", "").strip()
                        desc1     = tb.get("DRAWING_DESCRIPTION_1", "").strip()
                        desc2     = tb.get("DRAWING_DESCRIPTION_2", "").strip()
                        title_desc = f"{desc1} {desc2}".strip() if desc2 else desc1
                        if title_rev:
                            print(f"    [dwg-rev] block {ename!r} → REVISION={title_rev!r}")
                except Exception:
                    pass

            # ── Title block — fallback: any block with a REVISION attribute ──
            # Catches title block names other than "A1 XSTRATA" / "A1XSTRATA".
            elif not title_rev:
                try:
                    if ent.HasAttributes:
                        tb_fb = {a.TagString.upper(): a.TextString
                                 for a in ent.GetAttributes()}
                        rev_cand = tb_fb.get("REVISION", "").strip()
                        if rev_cand:
                            title_rev = rev_cand
                            d1 = tb_fb.get("DRAWING_DESCRIPTION_1", "").strip()
                            d2 = tb_fb.get("DRAWING_DESCRIPTION_2", "").strip()
                            if not title_desc:
                                title_desc = f"{d1} {d2}".strip() if d2 else d1
                            print(f"    [dwg-rev] fallback block {ename!r}"
                                  f" → REVISION={title_rev!r}")
                except Exception:
                    pass

        if bom_found_here:
            print(f"    Layout {lname!r}: {bom_found_here} BOM row(s)")
        else:
            # Log block names so we can diagnose mismatches
            if seen_block_names:
                names_sorted = sorted(seen_block_names)
                print(f"    Layout {lname!r}: no BOM blocks — blocks present: "
                      + ", ".join(repr(n) for n in names_sorted[:20])
                      + (" …" if len(names_sorted) > 20 else ""))

    if not bom_rows:
        print("    No 'XT Item' blocks found in any layout.")
        return None

    # ── Initial y-sort — gives a stable read order for the debug log ─────────
    # The definitive sort is by ITEM number (below) after the rows are built;
    # this y-pass just keeps the debug printout tidy.
    bom_rows.sort(key=lambda r: r[0])

    print(f"    BOM rows extracted : {len(bom_rows)}")
    if title_rev:
        print(f"    Title block rev    : {title_rev!r}")
    if title_desc:
        print(f"    Title block desc   : {title_desc!r}")

    # ── Build normalised row dicts (same shape as extract_bom_from_pdf rows) ──
    group = []
    for y, attrs in bom_rows:
        item_text = attrs.get("ITEM",        "").strip()
        qty       = attrs.get("QTY",         "").strip()
        desc      = attrs.get("DESCRIPTION", "").strip()
        spec      = attrs.get("JC-000000",   "").strip()

        # Fall back to sequential position if ITEM attribute is blank.
        if not item_text:
            item_text = str(len(group) + 1)

        print(f"      [{item_text:>4s}] y={y:7.2f}  qty={qty!r:5}  "
              f"desc={desc[:45]!r}  spec={spec[:30]!r}")

        group.append({
            "item_text": item_text,
            "item_y":    y,
            "cells":     [item_text, qty, desc, spec],
        })

    # Filter out blank rows before deduplication.
    # The BOM block definition itself is inserted as a template at the bottom of
    # the table with all attributes empty (or containing just the item number).
    # Removing it here prevents the deduplicator from keeping the empty version
    # of an item and discarding the real data row above it.
    group = [r for r in group if r["cells"][1] or r["cells"][2] or r["cells"][3]]

    # Deduplicate by item text — keep the first occurrence.
    seen_items: set = set()
    deduped = []
    for row in group:
        if row["item_text"] not in seen_items:
            seen_items.add(row["item_text"])
            deduped.append(row)

    # ── Sort by item number ascending (same fix as Inventor extractor) ────────
    # Sorting by y-coordinate alone is unreliable — some drawings have the BOM
    # oriented so that item 1 is at the top (highest y) rather than the bottom.
    # Extracting the leading digits from the ITEM attribute text and sorting
    # numerically is layout-independent and matches the Inventor script approach.
    # Sub-items (5a, 5b …) sort after their parent because the leading digit
    # comparison puts them after 5 and before 6.  Rows with no digits get 9999.
    deduped.sort(key=lambda r: _dwg_item_number(r["item_text"]))

    col_map = {"Item": 0, "QTY": 1, "Description": 2, "Specification": 3}

    return {
        "drawing":    drawing,
        "col_map":    col_map,
        "raw_cols":   ["ITEM", "QTY", "DESCRIPTION", "JC-000000"],
        "bom_groups": [deduped],
        "title_rev":  title_rev,
        "title_desc": title_desc,
    }


# ============================================================
#  EXCEL OUTPUT  (mirrors iLogic v18 AppendBlock layout)
# ============================================================

def _get_cell_value(row_cells, col_idx):
    if col_idx is None or col_idx >= len(row_cells):
        return ""
    return row_cells[col_idx].strip()


def _apply_block_format(ws, start_row, item_count):
    """
    Format one block:
      start_row   : column header row  (Rev | Item | QTY | Description | Specification)
      start_row+1 : banner row         (rev | drawing_name | merged | | green fill)
      start_row+2 onwards: data rows
    """
    # --- Header row ---
    for c in range(1, 6):
        cell = ws.cell(row=start_row, column=c)
        cell.font      = _FONT_HEADER
        cell.alignment = _ALIGN_CTR
        cell.border    = _BORDER if c > 1 else _THICK_LEFT

    # --- Banner row ---
    banner_row = start_row + 1
    for c in range(1, 6):
        cell = ws.cell(row=banner_row, column=c)
        cell.font   = _FONT_BANNER
        cell.fill   = _GREEN_FILL
        cell.border = _BORDER if c > 1 else _THICK_LEFT
    ws.cell(row=banner_row, column=1).alignment = _ALIGN_CTR
    ws.cell(row=banner_row, column=2).alignment = _ALIGN_LEFT
    try:
        ws.merge_cells(start_row=banner_row, start_column=2,
                       end_row=banner_row,   end_column=4)
    except Exception:
        pass

    # --- Data rows ---
    if item_count > 0:
        for r in range(start_row + 2, start_row + 2 + item_count):
            for c in range(1, 6):
                cell = ws.cell(row=r, column=c)
                cell.font   = _FONT_DATA
                cell.border = _BORDER if c > 1 else _THICK_LEFT
            ws.cell(row=r, column=2).alignment = _ALIGN_CTR
            ws.cell(row=r, column=3).alignment = _ALIGN_CTR


def last_used_row(ws):
    """Return the last row index that has any content in columns A–E."""
    last = 0
    for row in ws.iter_rows(min_col=1, max_col=5):
        for cell in row:
            if cell.value not in (None, ""):
                last = cell.row
    return last


def append_block(ws, banner, data_rows, rev):
    """
    Write one drawing block to the sheet.
    data_rows: list of [item, qty, desc, spec]
    """
    last = last_used_row(ws)
    start = 1 if last == 0 else last + 3   # 2-blank-row gap (row gap = 3 incl header)

    # Column header row
    for c, heading in enumerate(["Rev", "Item", "QTY", "Description", "Specification"], start=1):
        ws.cell(row=start, column=c, value=heading)

    # Banner row — store rev as integer when it's a plain digit (avoids "Number
    # Stored as Text" warning in Excel for values like "1", "2", "3" etc.)
    try:
        rev_val = int(rev) if str(rev).strip().isdigit() else rev
    except (TypeError, ValueError):
        rev_val = rev
    ws.cell(row=start + 1, column=1, value=rev_val)
    ws.cell(row=start + 1, column=2, value=banner)

    # Data rows
    for i, row in enumerate(data_rows):
        r = start + 2 + i

        def _to_int(v):
            """Convert to int ONLY when the value is a plain positive integer
            with no leading zeros (e.g. item numbers 1, 2, 3 or qty 24).
            Codes with leading zeros like '00032405' must stay as text — Excel
            would silently drop the leading zeros if stored as a number."""
            s = str(v).strip()
            try:
                if s.isdigit() and (len(s) == 1 or s[0] != "0"):
                    return int(s)
            except (TypeError, ValueError):
                pass
            return s

        # Item and QTY — integers for plain numbers; text with format flag
        # for anything that starts with 0 or contains non-digit characters.
        for col_idx, val in ((2, row[0]), (3, row[1])):
            converted = _to_int(val)
            cell = ws.cell(row=r, column=col_idx, value=converted)
            if not isinstance(converted, int):
                cell.number_format = "@"
                cell.quotePrefix   = True

        # Description and Specification — always stored as text.
        # number_format "@" + quotePrefix suppresses the "Number Stored as
        # Text" green triangle on digit-only values like "00032405".
        c_desc = ws.cell(row=r, column=4, value=row[2])
        c_desc.number_format = "@"
        c_desc.quotePrefix   = True
        c_spec = ws.cell(row=r, column=5, value=row[3])
        c_spec.number_format = "@"
        c_spec.quotePrefix   = True

    _apply_block_format(ws, start, len(data_rows))


def already_there(ws, banner):
    """Return True if a banner cell with this text already exists in column B."""
    for row in ws.iter_rows(min_col=2, max_col=2):
        if str(row[0].value or "").strip().upper() == banner.strip().upper():
            return True
    return False


def open_or_create_workbook(working_path, template_path):
    """
    Always start from the template (copy → open).
    If template missing, create a blank workbook.
    Clears the BOM sheet data while preserving column widths from template.
    """
    # Delete old working file; always rebuild from template (v18 behaviour)
    wp = Path(working_path)
    if wp.exists():
        try:
            wp.unlink()
        except Exception:
            pass

    tp = Path(template_path)
    if tp.exists():
        try:
            shutil.copy2(str(tp), str(wp))
            wb = openpyxl.load_workbook(str(wp), keep_links=False)
        except Exception:
            wb = openpyxl.Workbook()
    else:
        wb = openpyxl.Workbook()

    # Find or create BOM sheet
    ws = None
    for sh in wb.sheetnames:
        if sh.upper() in ("BOM", "BOMS"):
            ws = wb[sh]
            break
    if ws is None:
        if wb.sheetnames:
            ws = wb.active
            ws.title = "BOM"
        else:
            ws = wb.create_sheet("BOM")

    # ClearContents: delete data but keep column widths baked into the template
    # Unmerge all existing ranges first (template merges clash with our banner merges)
    for merge_range in list(ws.merged_cells.ranges):
        ws.unmerge_cells(str(merge_range))
    # MergedCell slave cells are read-only — skip them
    from openpyxl.cell.cell import MergedCell
    for row in ws.iter_rows():
        for cell in row:
            if not isinstance(cell, MergedCell):
                cell.value = None

    # Column widths (template may have them; set defaults only if sheet is brand-new)
    if not tp.exists():
        ws.column_dimensions["A"].width = 6
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 8
        ws.column_dimensions["D"].width = 55
        ws.column_dimensions["E"].width = 42

    return wb, ws


def write_all(working_path, template_path, results, rev):
    """
    Write all drawing blocks to the working file.
    results: list of extract_bom_from_pdf() dicts.
    """
    Path(working_path).parent.mkdir(parents=True, exist_ok=True)
    wb, ws = open_or_create_workbook(working_path, template_path)

    added, skipped, missing = [], [], []

    for result in results:
        drawing    = result["drawing"]
        col_map    = result["col_map"]
        bom_groups = result.get("bom_groups") or []

        if not bom_groups:
            missing.append(drawing)
            continue

        multi      = len(bom_groups) > 1   # two or more BOM tables on this drawing
        title_desc = result.get("title_desc", "")

        for g_idx, group in enumerate(bom_groups):
            # Banner: plain drawing name for a single BOM;
            # append "_BOM 1", "_BOM 2"… when the drawing has multiple tables.
            # Append the title block description (e.g. "LOWER FLOTATION GENERAL
            # ARRANGEMENT") when we extracted one, separated by " - ".
            banner = f"{drawing}_BOM {g_idx + 1}" if multi else drawing
            if title_desc:
                banner = f"{banner} - {title_desc}"

            if already_there(ws, banner):
                skipped.append(banner)
                continue

            # Build fixed-column data rows: [Item, QTY, Description, Specification]
            data_rows = []
            for row in group:
                cells = row["cells"]
                item_val = _get_cell_value(cells, col_map.get("Item"))
                qty_val  = _get_cell_value(cells, col_map.get("QTY"))
                desc_val = _get_cell_value(cells, col_map.get("Description"))
                spec_val = _get_cell_value(cells, col_map.get("Specification"))

                # ITEM column overflow repair — large bulk-fastener quantities
                # (e.g. 128, 168, 256) are right-aligned in Inventor BOMs so
                # their LEFT edge falls inside the ITEM band (x < 1732.0) rather
                # than in the QTY band.  Both the real item number and the qty
                # integer end up concatenated in item_val (e.g. "13 128").
                # Detect: item_val = "<integer> <integer>" → strip the trailing
                # integer, prepend it to qty_val so the QTY overflow repair below
                # can split it correctly (e.g. qty_val becomes "128 M16").
                item_overflow = re.match(r'^(\d+)\s+(\d+)\s*$', item_val)
                if item_overflow:
                    item_val  = item_overflow.group(1)
                    qty_extra = item_overflow.group(2)
                    qty_val   = (qty_extra + ' ' + qty_val).strip() if qty_val else qty_extra

                # QTY overflow repair — Inventor PDFs: the description's first
                # word(s) can land in the QTY band because the ITEM/QTY columns
                # share a single merged header and description text starts
                # immediately after the QTY value at nearly the same x.
                #
                # Case A — "<integer> <word(s)>": the integer is the real QTY;
                #   everything after the first space belongs to description.
                #   E.g. qty='12 M16', desc='x 45 BOLT' → qty=12, desc='M16 x 45 BOLT'
                #
                # Case B — pure text, no leading integer: the entire qty_val is
                #   the start of the description (e.g. qty='SINGLE', qty='SEE NOTE 5').
                #   These items have no explicit numeric quantity on the drawing;
                #   preserve the text as qty (it may be meaningful like "SEE NOTE 5")
                #   only when it looks intentional, otherwise prepend to description.
                #   Rule: if qty_val is ALL letters/spaces (no digits at all) and is
                #   not a recognised special token, treat it as description overflow.
                qty_overflow = re.match(r'^(\d+)\s+(.+)$', qty_val)
                if qty_overflow:
                    qty_val  = qty_overflow.group(1)
                    prefix   = qty_overflow.group(2)
                    desc_val = (prefix + " " + desc_val).strip() if desc_val else prefix
                elif qty_val and not re.search(r'\d', qty_val):
                    # Pure-text QTY — no digit at all.
                    # Keep recognised special tokens (SEE NOTE …, TBC, N/A, etc.)
                    # as the qty value; treat everything else as description overflow.
                    _SEE_NOTE = re.match(
                        r'^(SEE\s+NOTE\s*\d*|TBC|TBD|N/?A|AS\s+REQ|VAR)',
                        qty_val, re.IGNORECASE)
                    # Case B2 — "NOTE" alone with "SEE" lost to the ITEM band:
                    #   ITEM='SEE'  QTY='NOTE'  DESC='5 HILTI X-FCM ...'
                    # Reconstruct as qty='SEE NOTE 5', desc='HILTI X-FCM ...'
                    _NOTE_SPLIT = (
                        not _SEE_NOTE
                        and qty_val.upper() == 'NOTE'
                        and re.match(r'^\d+\b', desc_val)
                    )
                    if _NOTE_SPLIT:
                        _n = re.match(r'^(\d+)\s*(.*)', desc_val)
                        qty_val  = f'SEE NOTE {_n.group(1)}'
                        desc_val = _n.group(2).strip()
                    elif not _SEE_NOTE:
                        # e.g. qty='SINGLE', qty='THREE', qty='FOUR'
                        desc_val = (qty_val + " " + desc_val).strip() if desc_val else qty_val
                        qty_val  = ''

                # Mass suffix strip — the merged SPECIFICATION MASS (EA) column
                # appends mass at the end of every spec value.  Patterns seen:
                #   "JC004073 3770 kg"   →  full "kg"
                #   "PJ00197-... 35 k"   →  truncated "k" (column ran out of space)
                #   "PJ00197-... 497 "   →  number only (unit truncated entirely)
                # Strip: one or more spaces, a number (int/float), optional unit
                # (kg / k / lbs / lb), anchored at string end.  The leading \s+
                # prevents stripping trailing digits in part numbers like JC000084.
                if spec_val and '&' in spec_val:
                    print(f"      [post-DEBUG] spec_val entering mass-strip: {spec_val!r}")
                if spec_val:
                    _spec_before_post = spec_val
                    spec_val = re.sub(
                        r'\s+\d[\d.,]*\s*(?:k(?:g)?|lbs?|lb)?\s*$',
                        '', spec_val, flags=re.IGNORECASE).strip()
                    # Also handle the case where spec IS entirely a mass value
                    # (e.g. "11 kg") — the leading-\s+ pattern above won't fire.
                    spec_val = re.sub(
                        r'^\d[\d.,]*\s*(?:k(?:g)?|lbs?|lb)?\s*$',
                        '', spec_val, flags=re.IGNORECASE).strip()
                    if _spec_before_post != spec_val and '&' in _spec_before_post:
                        print(f"      [post-DEBUG] mass-strip changed &-spec: {_spec_before_post!r} → {spec_val!r}")

                # Spec-prefix overflow — when the DESCRIPTION text ends with a
                # parenthesised dimension (e.g. "(2330mm)", "(1165mm)") that spills
                # into the SPEC band, the spec_val begins with that token.
                # After the mass strip the spec may look like "(2330mm) -" or
                # "(363 mm) GALVANISED".  Reclaim the parenthesised prefix back
                # onto description and leave only the genuine spec value.
                # Only fires on merged-column drawings (those that reach this path).
                if spec_val:
                    _dim_prefix = re.match(
                        r'^(\([^)]{1,20}\))\s*(.*)', spec_val)
                    if _dim_prefix:
                        desc_val = (desc_val + " " + _dim_prefix.group(1)).strip()
                        spec_val = _dim_prefix.group(2).strip()
                        # Remove a bare leading "-" that was the original spec value
                        # when the real spec is "-" (handrail items)
                        if spec_val == '-':
                            spec_val = '-'   # keep as-is — it IS the spec

                # Also reclaim a bare hyphen-dimension prefix that spills from
                # description into the spec column, e.g. "- 3381mm PLAIN CARBON STEEL"
                # → description gets "- 3381mm", spec becomes "PLAIN CARBON STEEL".
                # Only fires when the prefix is solely a dimension fragment (no other
                # spec text before it).
                if spec_val:
                    _hyph_dim = re.match(
                        r'^(-\s*\d[\d.,]*\s*mm)\s+(.*)', spec_val, re.IGNORECASE)
                    if _hyph_dim:
                        desc_val = (desc_val + " " + _hyph_dim.group(1)).strip()
                        spec_val = _hyph_dim.group(2).strip()

                # Split-parenthetical join — a dimension token like "(2358 mm)" can
                # be cut at the column boundary: desc ends with the open half
                # "(2358" and spec begins with the close half "mm)".
                # Rejoin with a space: desc="…(2358 mm)", spec="GALVANISED".
                if desc_val and spec_val:
                    _split_open  = re.search(r'\(\d[\d.]*\s*$', desc_val)
                    _split_close = re.match(r'^([a-z]{1,5}\))', spec_val, re.IGNORECASE)
                    if _split_open and _split_close:
                        desc_val = desc_val.rstrip() + ' ' + _split_close.group(1)
                        spec_val = spec_val[len(_split_close.group(1)):].strip()

                # Description-overflow reclaim — long description text can overflow
                # past the x=1916.2 divider and land at the start of the spec cell.
                # Move those leading word(s) back to description when the first
                # recognisable spec anchor (part number, standard, instrument tag)
                # is not the very first word.
                _spec_before_reclaim = spec_val
                desc_val, spec_val = _reclaim_spec_overflow(desc_val, spec_val)
                if _spec_before_reclaim != spec_val and '&' in _spec_before_reclaim:
                    print(f"      [post-DEBUG] _reclaim changed &-spec: {_spec_before_reclaim!r} → {spec_val!r}")

                data_rows.append([item_val, qty_val, desc_val, spec_val])

            append_block(ws, banner, data_rows, rev)
            added.append(banner)
            print(f"    -> Written: {banner} ({len(data_rows)} item(s))")

    # Strip all defined names (named ranges) before saving — they come from the
    # template and openpyxl can't round-trip them cleanly, which causes Excel's
    # "Removed Records: Named range" repair dialog on every open.
    # Strip all defined names (named ranges) before saving — they come from the
    # template and openpyxl can't round-trip them cleanly, which causes Excel's
    # "Removed Records: Named range" repair dialog on every open.
    try:
        wb.defined_names.clear()
    except Exception:
        pass

    # Try the primary path; if it is open in Excel (PermissionError) try
    # numbered variants (_1, _2, …) so the user can keep the old file open
    # for comparison while the new result lands beside it.
    _saved_path = None
    _wp = Path(working_path)
    for _suffix in [""] + [f"_{i}" for i in range(1, 10)]:
        _candidate = _wp.with_stem(_wp.stem + _suffix) if _suffix else _wp
        try:
            wb.save(str(_candidate))
            _saved_path = _candidate
            break
        except PermissionError:
            continue
        except Exception as e:
            print(f"\n  ERROR saving workbook: {e}")
            break
    if _saved_path:
        print(f"\n  Working file saved: {_saved_path}")
    else:
        print(f"\n  ERROR: could not save workbook — all candidate paths are locked")

    return added, skipped, missing


# ============================================================
#  MAIN
# ============================================================

def _drawing_sort_key(result):
    """
    Sort key for BOM results by drawing number.
    Extracts the last dash-separated segment (e.g. '000010' from
    'PJ00193-GTA-3420-6-000010') and sorts numerically so that
    000001 < 000003 < 000010 regardless of insertion order.
    """
    stem = result.get("drawing", "")
    # Use stem without path/extension
    stem = Path(stem).stem if Path(stem).suffix else stem
    parts = stem.split("-")
    last  = parts[-1] if parts else stem
    # Numeric sort if possible, else lexicographic fallback
    try:
        return (0, int(last), "")
    except ValueError:
        return (1, 0, last.upper())


def _run_pdf_pass(pdf_files, fab_skip, no_bom, failed):
    """
    Extract BOMs from a list of PDF paths.
    Returns (good_results, shx_results) where:
      good_results — PDFs with a native text layer (used_ocr=False)
      shx_results  — PDFs that needed OCR (used_ocr=True); caller decides
                     whether to replace these with DWG extractions.
    """
    good_results = []
    shx_results  = []

    for pdf_path in pdf_files:
        stem = Path(pdf_path).stem
        try:
            result = extract_bom_from_pdf(pdf_path)
            if result:
                if result.get("used_ocr"):
                    shx_results.append(result)
                else:
                    good_results.append(result)
            else:
                no_bom.append(Path(pdf_path).name)
        except Exception:
            print(f"  UNHANDLED ERROR on {Path(pdf_path).name}:\n"
                  + traceback.format_exc())
            failed.append(Path(pdf_path).name)

    return good_results, shx_results


def _is_inventor_dwg(path) -> bool:
    """Return True if *path* is a DWG saved by Autodesk Inventor.

    Inventor embeds the string "Autodesk Inventor" in the binary of every
    DWG it saves (in the APPINFO / header comment area).  AutoCAD-native
    DWGs never contain this string.

    The string may be stored as ASCII/UTF-8 bytes OR as UTF-16LE wide
    characters (common in newer Inventor versions).  We check both.
    Reading 512 KB catches all known header layouts.
    """
    _ASCII  = b"Autodesk Inventor"
    _UTF16  = "Autodesk Inventor".encode("utf-16-le")   # wide-char variant
    try:
        with open(path, "rb") as fh:
            blob = fh.read(524288)  # 512 KB
        return (_ASCII in blob) or (_UTF16 in blob)
    except Exception:
        return False          # if we can't read, fall through to normal logic


def _run_dwg_pass(dwg_paths, allowed_stems, fab_skip, no_bom, failed):
    """
    Extract BOMs from DWG files.

    Routing:
      .idw extension          → always Inventor COM
      .dwg with Inventor sig  → Inventor COM (binary sniff: "Autodesk Inventor"
                                in first 64 KB); falls back to AutoCAD on failure
      .dwg without signature  → AutoCAD COM directly (skips Inventor entirely)

    A DWG without a BOM in either app is logged to no_bom and silently skipped.
    allowed_stems=None means process all files; otherwise filters to that set.
    Returns list of result dicts.
    """
    # ── Connect to AutoCAD once for the whole pass ────────────────────────────
    # If AutoCAD is already open we reuse it; if not, we launch it and close it
    # automatically when the pass is done (so we don't leave a ghost instance).
    _acad_instance, _acad_launched = _connect_autocad()

    results = []
    for dwg_path in dwg_paths:
        stem   = Path(dwg_path).stem
        suffix = Path(dwg_path).suffix.lower()
        if allowed_stems is not None:
            if stem.upper() not in {s.upper() for s in allowed_stems}:
                print(f"  {stem}  [SKIPPED — not in SHX replacement list]")
                continue
        result = None

        # ── Routing for .dwg files ────────────────────────────────────────────
        # .idw              → Inventor COM only
        # .dwg  sniff=True  → Inventor COM first; AutoCAD fallback if Inventor
        #                      fails or returns no BOM (handles rare false-positive
        #                      where an AutoCAD DWG embeds an Inventor string)
        # .dwg  sniff=False → AutoCAD COM first; Inventor fallback if no BOM found
        if suffix == ".dwg":
            _sniff_inv = _is_inventor_dwg(dwg_path)
            print(f"  {stem}  [DWG — {'Inventor sig detected' if _sniff_inv else 'AutoCAD'}]")

        # ── Inventor COM (primary for .idw and sniff-positive .dwg) ──────────
        if suffix == ".idw" or (suffix == ".dwg" and _sniff_inv):
            try:
                result = extract_bom_from_inventor(dwg_path)
                if result:
                    _label = "Inventor COM ✓" if suffix == ".idw" else "Inventor COM ✓  (Inventor DWG)"
                    print(f"  {stem}  [{_label}]")
            except Exception as exc_inv:
                inv_err = str(exc_inv)
                print(f"  {stem}  Inventor COM failed ({inv_err[:80]})")
                result = None

        # ── AutoCAD COM ───────────────────────────────────────────────────────
        # Primary for sniff-negative .dwg; fallback for sniff-positive .dwg
        # when Inventor failed or found no BOM.
        if suffix == ".dwg" and not result:
            _acad_label = "AutoCAD COM (fallback)" if _sniff_inv else "AutoCAD COM"
            try:
                result = extract_bom_from_dwg(dwg_path, acad=_acad_instance)
                if result:
                    print(f"  {stem}  [{_acad_label} ✓]")
            except Exception:
                print(f"  UNHANDLED ERROR on {Path(dwg_path).name}:\n"
                      + traceback.format_exc())
                failed.append(Path(dwg_path).name)
                continue

        if result:
            results.append(result)
        else:
            print(f"  {stem}  [no BOM found — skipped]")
            no_bom.append(Path(dwg_path).name)

    # ── Close AutoCAD if we launched it ──────────────────────────────────────
    if _acad_launched and _acad_instance is not None:
        try:
            _acad_instance.Quit()
            print("  [AutoCAD closed — was launched only for this run]")
        except Exception:
            pass

    return results


# ---------------------------------------------------------------------------
# PDF vs DWG comparison
# ---------------------------------------------------------------------------

def compare_pdf_dwg(working_folder: str) -> None:
    """Load *_PDF.xlsx and *_DWG.xlsx from working_folder, compare row by row,
    write a side-by-side diff to BomExtractor_compare.txt and show a popup.

    Rows are keyed on (drawing_sheet, item_number).  Differences in QTY or
    Specification are flagged.  Items present in one file but not the other are
    listed as ONLY-IN-PDF or ONLY-IN-DWG.
    """
    import glob as _glob

    folder = Path(working_folder)
    pdf_files = sorted(folder.glob("*_PDF.xlsx"))
    dwg_files = sorted(folder.glob("*_DWG.xlsx"))

    if not pdf_files:
        show_message("Compare PDF vs DWG", "No *_PDF.xlsx found in working folder.\nRun a PDF extraction first.")
        return
    if not dwg_files:
        show_message("Compare PDF vs DWG", "No *_DWG.xlsx found in working folder.\nRun a DWG extraction first.")
        return

    pdf_path = pdf_files[-1]   # most recent
    dwg_path = dwg_files[-1]

    def _load_xlsx(path):
        """Return dict: sheet_name → list of (item, qty, desc, spec) tuples."""
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        data = {}
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue
            # Find the header row (contains ITEM or item)
            header_idx = None
            for i, row in enumerate(rows):
                cells = [str(c).strip().upper() if c else "" for c in row]
                if "ITEM" in cells:
                    header_idx = i
                    break
            if header_idx is None:
                continue
            header = [str(c).strip().upper() if c else "" for c in rows[header_idx]]
            def _col(names):
                for n in names:
                    if n in header:
                        return header.index(n)
                return None
            ci = _col(["ITEM"])
            cq = _col(["QTY", "QUANTITY"])
            cd = _col(["DESCRIPTION"])
            cs = _col(["SPECIFICATION", "PART NO. / SPECIFICATION", "PART NO./SPECIFICATION"])
            if ci is None:
                continue
            sheet_rows = []
            for row in rows[header_idx + 1:]:
                if not any(row):
                    continue
                def _get(idx):
                    if idx is None or idx >= len(row):
                        return ""
                    return str(row[idx]).strip() if row[idx] is not None else ""
                item = _get(ci)
                if not item or not item.replace(".", "").isdigit():
                    continue  # skip non-data rows
                sheet_rows.append((item, _get(cq), _get(cd), _get(cs)))
            if sheet_rows:
                data[ws.title] = sheet_rows
        wb.close()
        return data

    print(f"\nComparing:\n  PDF: {pdf_path.name}\n  DWG: {dwg_path.name}")
    pdf_data = _load_xlsx(pdf_path)
    dwg_data = _load_xlsx(dwg_path)

    out_lines = [
        "=" * 70,
        f"BOM COMPARISON REPORT — {datetime.datetime.now():%Y-%m-%d %H:%M}",
        f"  PDF: {pdf_path.name}",
        f"  DWG: {dwg_path.name}",
        "=" * 70,
    ]

    all_sheets = sorted(set(list(pdf_data.keys()) + list(dwg_data.keys())))
    total_diffs = 0

    for sheet in all_sheets:
        pdf_rows = pdf_data.get(sheet, [])
        dwg_rows = dwg_data.get(sheet, [])

        if not pdf_rows and not dwg_rows:
            continue

        # Key by item number (normalised)
        def _norm_item(i):
            return i.lstrip("0") or "0"

        pdf_map = {_norm_item(r[0]): r for r in pdf_rows}
        dwg_map = {_norm_item(r[0]): r for r in dwg_rows}

        all_items = sorted(
            set(list(pdf_map.keys()) + list(dwg_map.keys())),
            key=lambda x: float(x) if x.replace(".", "").isdigit() else 0
        )

        sheet_diffs = []
        for item in all_items:
            pr = pdf_map.get(item)
            dr = dwg_map.get(item)
            if pr is None:
                sheet_diffs.append(f"  Item {item:>4}  ONLY-IN-DWG   qty={dr[1]}  spec={dr[3]}")
            elif dr is None:
                sheet_diffs.append(f"  Item {item:>4}  ONLY-IN-PDF   qty={pr[1]}  spec={pr[3]}")
            else:
                diffs = []
                if pr[1].strip().upper() != dr[1].strip().upper():
                    diffs.append(f"QTY  PDF={pr[1]!r}  DWG={dr[1]!r}")
                if pr[3].strip().upper() != dr[3].strip().upper():
                    diffs.append(f"SPEC PDF={pr[3]!r}  DWG={dr[3]!r}")
                if diffs:
                    sheet_diffs.append(f"  Item {item:>4}  DIFFERS  {' | '.join(diffs)}")

        if sheet_diffs:
            out_lines.append(f"\n[{sheet}]  ({len(pdf_rows)} PDF rows / {len(dwg_rows)} DWG rows)")
            out_lines.extend(sheet_diffs)
            total_diffs += len(sheet_diffs)
        else:
            if pdf_rows or dwg_rows:
                out_lines.append(f"\n[{sheet}]  ✓ MATCH  ({len(pdf_rows)} rows)")

    out_lines += [
        "",
        "=" * 70,
        f"Total differences found: {total_diffs}",
        "=" * 70,
    ]

    report = "\n".join(out_lines)
    print(report)

    report_path = folder / "BomExtractor_compare.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nComparison report saved: {report_path}")

    summary = f"{total_diffs} difference(s) found across {len(all_sheets)} drawing(s).\n\nReport saved to:\n{report_path}"
    show_message("BOM Compare: PDF vs DWG", summary)


def main():
    # ── Pass 1: select PDFs and/or DWGs ──────────────────────────────────────
    all_paths = pick_files(
        title="Select drawing file(s) — PDF and/or DWG — hold Ctrl for multiple",
        filter_str=(
            "Drawing Files\0*.pdf;*.dwg\0"
            "PDF Files\0*.pdf\0"
            "AutoCAD / Inventor DWG Files\0*.dwg\0"
            "All Files\0*.*\0"
        ),
    )
    if not all_paths:
        print("No files selected — exiting.")
        return

    # Sort by filename
    all_paths.sort(key=lambda p: Path(p).name.upper())

    # Prefix filter — only process drawings in the same PJ#####-SITE-AREA- family
    first_stem = Path(all_paths[0]).stem
    prefix     = get_drawing_prefix(first_stem)
    filtered   = [p for p in all_paths
                  if Path(p).stem.upper().startswith(prefix.upper())]
    excluded   = [p for p in all_paths if p not in filtered]

    if excluded:
        print(f"\nPrefix filter ({prefix}): {len(excluded)} file(s) excluded:")
        for p in excluded:
            print(f"  {Path(p).name}")

    pdf_files = [p for p in filtered if Path(p).suffix.lower() == ".pdf"]
    dwg_files = [p for p in filtered if Path(p).suffix.lower() == ".dwg"]

    # ── 400-series prompt (DISABLED — 400-series drawings not included for now) ──
    # Re-enable this block when fab drawing BOMs are needed.
    # _fab_re = re.compile(r'-0004\d\d$', re.IGNORECASE)
    # _fab_pdfs  = [p for p in pdf_files  if _fab_re.search(Path(p).stem)]
    # _fab_dwgs  = [p for p in dwg_files  if _fab_re.search(Path(p).stem)]
    # if _fab_pdfs or _fab_dwgs:
    #     _fab_total = len(_fab_pdfs) + len(_fab_dwgs)
    #     _ans = ctypes.windll.user32.MessageBoxW(
    #         0,
    #         f"{_fab_total} 400-series fab drawing(s) are included in this selection.\n\n"
    #         "Include 400 Fab Drawing BOMs?",
    #         "Include Fab Drawings?",
    #         4   # MB_YESNO
    #     )
    #     if _ans != 6:   # not IDYES → exclude them
    #         pdf_files = [p for p in pdf_files if p not in _fab_pdfs]
    #         dwg_files = [p for p in dwg_files if p not in _fab_dwgs]
    #         print(f"[400-series excluded: {_fab_total} drawing(s) skipped by user choice]")
    # ── Always exclude 400-series until re-enabled above ─────────────────────
    _fab_re = re.compile(r'-0004\d\d$', re.IGNORECASE)
    _fab_pdfs  = [p for p in pdf_files  if _fab_re.search(Path(p).stem)]
    _fab_dwgs  = [p for p in dwg_files  if _fab_re.search(Path(p).stem)]
    if _fab_pdfs or _fab_dwgs:
        pdf_files = [p for p in pdf_files if p not in _fab_pdfs]
        dwg_files = [p for p in dwg_files if p not in _fab_dwgs]
        print(f"[400-series excluded: {len(_fab_pdfs) + len(_fab_dwgs)} drawing(s) — 400-series disabled]")

    if not pdf_files and not dwg_files:
        show_message("BOM Extractor", f"No PDF or DWG files match the drawing prefix: {prefix}", error=True)
        return

    _start_time = time.perf_counter()

    # ── Start log tee (mirrors all console output to a file) ──────────────────
    if pdf_files and not dwg_files:
        _log_name = LOG_FILE_PDF
    elif dwg_files and not pdf_files:
        _log_name = LOG_FILE_DWG
    else:
        _log_name = LOG_FILE_MIX
    _log_path = str(Path(WORKING_FOLDER) / _log_name)
    _tee = _Tee(_log_path)
    print(f"Log file: {_log_path}")
    print(f"Build   : {BUILD_MARKER}")
    print("=" * 60)

    # Paths
    working_path  = str(Path(WORKING_FOLDER) / WORKING_FILENAME)
    template_path = str(Path(WORKING_FOLDER) / TEMPLATE_FILENAME)

    if pdf_files:
        print(f"\n{len(pdf_files)} PDF(s) selected (prefix: {prefix}):")
        for p in pdf_files:
            print(f"    {Path(p).name}")
    if dwg_files:
        print(f"\n{len(dwg_files)} DWG(s) selected (prefix: {prefix}):")
        for p in dwg_files:
            print(f"    {Path(p).name}")
    print(f"\nWorking file : {working_path}")
    print(f"Template     : {template_path}")
    print("=" * 60)

    no_bom   = []
    failed   = []
    fab_skip = []

    # ── PDF extraction ────────────────────────────────────────────────────────
    good_results  = []
    shx_results   = []
    if pdf_files:
        good_results, shx_results = _run_pdf_pass(pdf_files, fab_skip, no_bom, failed)

    shx_stems = {Path(r["drawing"]).stem if Path(r["drawing"]).suffix
                 else r["drawing"]
                 for r in shx_results}

    # ── DWG pass — pre-selected DWGs (Inventor or AutoCAD COM) ───────────────
    dwg_results = []
    if dwg_files:
        print(f"\n  DWG pass — {len(dwg_files)} file(s) pre-selected:")
        for p in dwg_files:
            print(f"    {Path(p).name}")
        print("=" * 60)
        # Use all pre-selected DWGs; shx_stems=None means no stem filter applied
        dwg_results = _run_dwg_pass(dwg_files, allowed_stems=None,
                                    fab_skip=fab_skip, no_bom=no_bom, failed=failed)

    # ── SHX popup + optional DWG supplement (for SHX PDFs not covered above) ──
    shx_stems_uncovered = shx_stems - {Path(r["drawing"]).stem for r in dwg_results}
    if shx_stems_uncovered:
        shx_names_sorted = sorted(shx_stems_uncovered)
        shx_list = "\n".join(f"  • {n}" for n in shx_names_sorted)
        shx_msg = (
            "The following PDF drawing(s) used OCR because they contain\n"
            "SHX / rasterised text (AutoCAD's older font format):\n\n"
            f"{shx_list}\n\n"
            "These drawings will be OMITTED from the Excel output.\n\n"
            "Click OK, then select the native AutoCAD .DWG file(s) for\n"
            "these drawings to get accurate BOM data.\n\n"
            "TIP: You can select ALL .dwg files in the folder — the script\n"
            "will only use the ones listed above."
        )
        show_message("SHX Drawing(s) Detected", shx_msg)

        print(f"\n  SHX drawings detected ({len(shx_stems_uncovered)}): {', '.join(shx_names_sorted)}")
        print("  Opening DWG picker for SHX supplement...")

        dwg_paths = pick_dwgs_for_shx(shx_names_sorted)
        if dwg_paths:
            dwg_paths.sort(key=lambda p: Path(p).name.upper())
            print(f"\n  DWG pass — {len(dwg_paths)} file(s) selected "
                  f"(filtering to SHX stems only):")
            for p in dwg_paths:
                print(f"    {Path(p).name}")
            print("=" * 60)
            shx_dwg_results = _run_dwg_pass(dwg_paths, shx_stems_uncovered,
                                            fab_skip, no_bom, failed)
            dwg_results = dwg_results + shx_dwg_results
        else:
            print("  DWG picker cancelled — SHX drawings will be omitted.")
            # Log omitted SHX drawings as no_bom
            for stem in shx_names_sorted:
                no_bom.append(f"{stem}.pdf  [SHX — no DWG provided]")

    # ── Combine + sort by drawing number ──────────────────────────────────────
    all_results = good_results + dwg_results
    all_results.sort(key=_drawing_sort_key)

    print("=" * 60)

    if not all_results:
        msg = (
            "No BOM data found in any of the selected file(s).\n\n"
            "PDF: make sure the drawing has a BOM table with ITEM, QTY,\n"
            "and DESCRIPTION column headers.\n"
            "SHX / rasterised AutoCAD PDFs need Tesseract OCR —\n"
            "install from https://github.com/UB-Mannheim/tesseract/wiki\n\n"
            "DWG (AutoCAD): AutoCAD must be installed; the DWG must\n"
            "contain 'XT Item Description Line' attribute blocks in\n"
            "a paper space layout."
        )
        print("\n" + msg)
        show_message("BOM Extractor", msg, error=True)
        return

    # Rev — from the first result's title block; fall back to "0"
    rev = next((r["title_rev"] for r in all_results if r.get("title_rev")), "")
    if rev:
        print(f"\n  Rev (title block)  : {rev}")
    else:
        rev = "0"
        print(f"\n  Rev                : {rev}  (not found in title block — using default)")

    # ── Write Excel ───────────────────────────────────────────────────────────
    print("\nWriting working file...")
    added, skipped, missing_write = write_all(working_path, template_path, all_results, rev)

    # Save named copy — suffix reflects what file types were actually selected
    if pdf_files and not dwg_files:
        source_suffix = "_PDF"
    elif dwg_files and not pdf_files:
        source_suffix = "_DWG"
    else:
        source_suffix = ""   # mixed selection — no suffix
    copy_path = save_named_copy(working_path, first_stem, rev, source_suffix)

    # Open BOM folder in Explorer + open named copy
    if copy_path and Path(copy_path).exists():
        bom_folder = str(Path(copy_path).parent)
        open_in_explorer(bom_folder)
        open_in_excel(copy_path)
    else:
        open_in_explorer(WORKING_FOLDER)

    # ── Summary ───────────────────────────────────────────────────────────────
    total_items = sum(len(g) for r in all_results for g in r.get("bom_groups", []))
    lines = [
        f"Rev          : {rev}",
        f"Added        : {len(added)}",
        f"Skipped      : {len(skipped)}  (already in sheet)",
        f"No BOM found : {len(no_bom)}",
        f"Fab 4xx skip : {len(fab_skip)}",
        f"Total items  : {total_items}",
        "",
        f"Working file : {working_path}",
        f"Named copy   : {copy_path or '(not saved)'}",
        "",
        f"Build        : {BUILD_MARKER}",
        f"Time taken   : {time.perf_counter() - _start_time:.1f}s",
    ]
    if shx_stems and not dwg_results:
        lines += ["\nSHX drawings omitted (no DWG provided):"] \
               + [f"  {n}" for n in sorted(shx_stems)]
    if no_bom:
        lines += ["\nNo BOM found in:"] + [f"  {n}" for n in no_bom]
    if failed:
        lines += ["\nFailed:"] + [f"  {n}" for n in failed]

    summary = "\n".join(lines)
    print("\n" + summary)
    print(f"\nLog saved to : {_log_path}")

    # Close log tee before showing the popup (popup is modal; tee must be flushed)
    try:
        _tee.close()
    except Exception:
        pass

    show_message("BOM Extractor Complete",
                 summary + f"\n\nLog saved to:\n{_log_path}")

    # ── Optional: compare PDF vs DWG if both outputs exist ──────────────────
    folder = Path(WORKING_FOLDER)
    has_pdf = any(folder.glob("*_PDF.xlsx"))
    has_dwg = any(folder.glob("*_DWG.xlsx"))
    if has_pdf and has_dwg:
        import ctypes
        want_compare = ctypes.windll.user32.MessageBoxW(
            0,
            "Both a _PDF.xlsx and a _DWG.xlsx were found.\n\nRun PDF vs DWG comparison now?",
            "Compare PDF vs DWG?",
            4   # MB_YESNO
        )
        if want_compare == 6:   # IDYES
            compare_pdf_dwg(WORKING_FOLDER)


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1].lower() in ("--compare", "-c", "compare"):
        # Standalone compare mode: python BomExtractorSweeper.py --compare
        compare_pdf_dwg(WORKING_FOLDER)
    else:
        main()
