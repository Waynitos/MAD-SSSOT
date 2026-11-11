# Adobe PDF Open Diagnostic — Specification
_Last updated: 2026-11-11_
**Status:** IMPLEMENTED; Windows/Adobe runtime not yet verified.

## Entry point
Run `py Adobe_PDF_Open_Diagnostic.py` on Windows with Python 3.9+ and psutil installed. A tkinter PDF file picker opens.

## Step-by-step flow
1. Ask operator to select one or more PDF files.
2. Create timestamped JSONL event and CSV process sample logs on Desktop.
3. For each PDF, launch via Windows file association (default PDF handler); record launch duration and any exception.
4. Monitor Acrobat/Reader process resource usage at approximately one-second intervals for 45 seconds.
5. Continue on per-process measurement errors; log failures rather than silently dropping them.
6. Close log files; report paths to operator. Never modify PDFs or Acrobat configuration.

## Key variable notes
| Variable | Meaning | Set where |
|---|---|---|
| `pdf_paths` | Selected PDF paths | tkinter file picker |
| `log_path` | JSONL event output | startup |
| `csv_path` | CSV sample output | startup |
| `fields` | CSV header schema, including `started` | startup |
| `SAMPLE_SECONDS` | Monitoring duration per PDF | module constant |

## Constraints
- Requires Windows and psutil; read-only monitoring except creating Desktop log files.
- Default PDF association may not be Acrobat; record that limitation.
- A launch request does not prove PDF render completion.
- CPU and disk counters may be unavailable or denied.
- Do not close, kill or alter Adobe processes.
- Keep one canonical script file; avoid version-suffixed duplicates.

## Commit history
| Commit | What |
|---|---|
| Initial | Add diagnostic with CSV schema fix for `started` field |
