# Scripts

Audited and patched scripts from MAD runs. Each script here has been through at least one full AA→DA→SSA cycle; the corresponding MAD run in `runs/` carries the full audit trail, findings, and fix rationale.

Use these as reference implementations when building new scripts that touch similar problem domains — the MAD output explains *why* each decision was made, not just what the code does.

## Index

| Script | Domain | MAD Run | Key Patterns |
|---|---|---|---|
| `spellcheck/SpellCheckOCR_Fallback_patched.py` | PDF OCR / SHX fonts | `runs/spellcheck-shx-audit/` | Tesseract subprocess with PSM 11, dual confidence thresholds, OCRPageProxy with synthetic dict, DPI calibration for CAD text |

## How to use as reference

1. Find the MAD run linked in the table above
2. Read `SSA-output.md` — the synthesis verdict explains which patterns are confirmed correct vs empirical/fragile
3. The AA output explains the strongest arguments *for* each design decision
4. The DA output explains where each pattern can fail and under what conditions

## Adding a new audited script

1. Place it under `scripts/<domain>/<ScriptName>_patched.py` (or `_v<date>.py` if versioned)
2. Add a row to the index table above
3. Link it from the corresponding `runs/<run-name>/README.md`
