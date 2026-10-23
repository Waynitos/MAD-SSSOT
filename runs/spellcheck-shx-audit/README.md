# MAD Run: SpellCheck SHX/OCR Audit

**Date:** 2026-10-24  
**Topic:** SpellCheckPDF_Word.py (v2026-10-23-merged-v15ag) + SpellCheckOCR_Fallback.py — SHX-font PDF handling audit  
**Files audited:** Two Python scripts for spell-checking engineering drawing PDFs  
**Cycle:** AA → DA → SSA + fix proposal  
**Session:** https://claude.ai/share/8e1a597d-bbc1-454c-b717-4d71fcb6864e

---

## Background

Engineering drawings exported from AutoCAD using legacy SHX (single-stroke vector) fonts produce PDFs where text exists as vector outlines rather than text objects. The tool currently handles this via two paths:

- **PDFSHX=1** (pure vector outlines): zero extractable text → OCR fallback via Tesseract subprocess
- **PDFSHX=2** (vector outlines + hidden text layer): text is extractable → per-word glyph-stroke filter removes false geometry crossings

This MAD run audited both paths for correctness and completeness.

---

## SSA Verdict (Summary)

**Architecture**: Sound. Two-path split is categorically correct.

**Implementation**: Four concrete bugs actively suppressing real findings:

1. **Tesseract called with PSM 3** (wrong for CAD title blocks — should be PSM 11 sparse text)
2. **300 DPI insufficient** for 2mm CAD text (24px; reliable floor is ~30px → need 400 DPI)
3. **OCRPageProxy incomplete** — `get_text("dict")` not intercepted (latent bug)
4. **No blank-page guard** — OCR fires on cover sheets and logo-only pages

**Structural gap**: Spelling 100% absent on PDFSHX=1 pages (the tool's primary function). Correct next feature to build after OCR accuracy improvements are validated.

**Migration path**: PyMuPDF `page.get_textpage_ocr()` (available since v1.21.0) replaces the entire subprocess pipeline — tracked as next architectural step after fixes 1–6 validated.

---

## Fixes (Priority Order)

| # | Fix | File | Effort | Risk |
|---|---|---|---|---|
| 1 | Add `--psm 11 --oem 1` to Tesseract subprocess call | SpellCheckOCR_Fallback.py | Small | Low |
| 2 | Raise `OCR_DPI` from 300 to 400 | SpellCheckOCR_Fallback.py | Small | Low |
| 3 | Split confidence threshold: 50 (standard text) / 30 (alphanumeric codes) | SpellCheckOCR_Fallback.py | Small | Medium |
| 4 | Add blank-page guard (50-segment heuristic before OCR trigger) | SpellCheckPDF_Word.py | Small | Low |
| 5 | Patch `OCRPageProxy.get_text("dict")` to return synthetic dict | SpellCheckOCR_Fallback.py | Small | Low |
| 6 | Raise SHX stroke threshold 0.36pt→0.50pt + circuit-breaker reporting | SpellCheckPDF_Word.py | Small | Low |

**Not in scope for this patch**: OCR spell-checking (requires calibration on real SHX drawings), `get_textpage_ocr()` migration (after fixes 1–6 validated).

---

## Files

| File | Contents |
|---|---|
| `AA-output.md` | Advocate: strongest case for the current two-path architecture |
| `DA-output.md` | Devil's Advocate: nine structural weaknesses with evidence |
| `SSA-output.md` | Synthesizer: tested verdict + copy-paste-ready code fixes for all six issues |

## Patched script

`scripts/spellcheck/SpellCheckOCR_Fallback_patched.py` — fixes 1–3 and 5 applied directly.
Fixes 4 and 6 target `SpellCheckPDF_Word.py` (main script); code snippets are in `SSA-output.md`.
