# Scripts

Audited and patched scripts from MAD runs. Each script here has been through at least one full AA→DA→SSA cycle; the corresponding MAD run in `runs/` carries the full audit trail, findings, and fix rationale.

Use these as reference implementations when building new scripts that touch similar problem domains — the MAD output explains *why* each decision was made, not just what the code does.

## Index

| Script | Domain | MAD Run | Key Patterns |
|---|---|---|---|
| `spellcheck/SpellCheckOCR_Fallback_patched.py` | PDF OCR / SHX fonts | `runs/spellcheck-shx-audit/` · [session](https://claude.ai/share/8e1a597d-bbc1-454c-b717-4d71fcb6864e) | Tesseract subprocess with PSM 11, dual confidence thresholds, OCRPageProxy with synthetic dict, DPI calibration for CAD text |
| `ilogic/TRAVERSE_fixed.iLogicVb` | Autodesk Inventor iLogic — assembly tree traversal & file rename | `runs/traverse-ilogic-audit/` · session TBD | 6-mode VB.NET rule: prefix swap, segment replace, consolidate, batch P-prefix scan, verify-only, Copy Design master; bottom-up traversal, Vault-aware, multi-phase Mode 2, performance cache, dual log files |

## How to use as reference

1. Find the MAD run linked in the table above
2. Read `SSA-output.md` — the synthesis verdict explains which patterns are confirmed correct vs empirical/fragile
3. The AA output explains the strongest arguments *for* each design decision
4. The DA output explains where each pattern can fail and under what conditions

## Adding a new audited script

1. Place it under `scripts/<domain>/<ScriptName>_patched.py` (or `_v<date>.py` if versioned)
2. Add a row to the index table above
3. Link it from the corresponding `runs/<run-name>/README.md`
