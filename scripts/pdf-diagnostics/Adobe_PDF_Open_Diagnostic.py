#!/usr/bin/env python3
"""BEEXCITED Adobe PDF Open Diagnostic — Windows, read-only process monitoring.

Requirements: Python 3.9+, psutil (py -m pip install psutil).
Opens selected PDFs using Windows' configured default PDF application.
Creates timestamped JSONL event and CSV sample logs on Desktop.
Does not measure exact page-render completion.
"""
import csv
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

SAMPLE_SECONDS = 45
SAMPLE_INTERVAL = 1.0
CSV_FIELDS = [
    "timestamp", "pdf_index", "pdf_name", "elapsed_s",
    "pid", "process_name", "cpu_percent", "rss_mb", "threads",
    "read_bytes", "write_bytes", "started"
]
ADOBE_NAMES = {"acrobat.exe", "acrord32.exe", "acrocef.exe", "rdrcef.exe"}


def desktop_folder():
    # OneDrive can redirect the Desktop; use the Windows Known Folder when available.
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            import uuid
            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                            ("Data3", wintypes.WORD), ("Data4", ctypes.c_byte * 8)]
            guid = uuid.UUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641")
            g = GUID.from_buffer_copy(guid.bytes_le)
            ptr = ctypes.c_wchar_p()
            shell = ctypes.windll.shell32
            shell.SHGetKnownFolderPath.argtypes = [
                ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
                ctypes.POINTER(ctypes.c_wchar_p)
            ]
            shell.SHGetKnownFolderPath.restype = ctypes.c_long
            result = shell.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(ptr))
            if result == 0 and ptr.value:
                folder = Path(ptr.value)
                ctypes.windll.ole32.CoTaskMemFree(ctypes.cast(ptr, ctypes.c_void_p))
                return folder
        except Exception:
            pass
    for folder in (Path.home() / "Desktop", Path.home() / "OneDrive" / "Desktop"):
        if folder.is_dir():
            return folder
    return Path.home()


def event(log, name, **details):
    entry = {"timestamp": dt.datetime.now().astimezone().isoformat(timespec="milliseconds"),
             "event": name, **details}
    log.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    log.flush()


def adobe_processes(psutil):
    found = []
    for proc in psutil.process_iter(["pid", "name", "create_time"]):
        try:
            if (proc.info.get("name") or "").lower() in ADOBE_NAMES:
                found.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found


def sample_process(psutil, proc, pdf_index, pdf_name, elapsed):
    info = proc.as_dict(attrs=["pid", "name", "memory_info", "num_threads", "create_time"],
                        ad_value=None)
    try:
        cpu = proc.cpu_percent(interval=None)
    except (psutil.Error, OSError):
        cpu = None
    try:
        io = proc.io_counters()
    except (psutil.Error, OSError):
        io = None
    memory = info.get("memory_info")
    return {
        "timestamp": dt.datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "pdf_index": pdf_index,
        "pdf_name": pdf_name,
        "elapsed_s": round(elapsed, 2),
        "pid": info.get("pid"),
        "process_name": info.get("name"),
        "cpu_percent": cpu,
        "rss_mb": round(memory.rss / (1024 * 1024), 2) if memory else None,
        "threads": info.get("num_threads"),
        "read_bytes": io.read_bytes if io else None,
        "write_bytes": io.write_bytes if io else None,
        "started": info.get("create_time")
    }


def main():
    if os.name != "nt":
        raise RuntimeError("This diagnostic is intended for Windows.")
    try:
        import psutil
    except ImportError:
        messagebox.showerror("Missing dependency",
                             "Install process monitoring first:\npy -m pip install psutil")
        return

    root = tk.Tk()
    root.withdraw()
    pdf_paths = filedialog.askopenfilenames(
        parent=root, title="Select PDF files to open and monitor",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    if not pdf_paths:
        root.destroy()
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    desktop = desktop_folder()
    log_path = desktop / ("Adobe_PDF_Diagnostic_" + stamp + ".jsonl")
    csv_path = desktop / ("Adobe_PDF_Diagnostic_" + stamp + "_samples.csv")

    with log_path.open("w", encoding="utf-8") as log, \
         csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS, extrasaction="raise")
        writer.writeheader()
        event(log, "session_start", python=sys.version, psutil=psutil.__version__,
              pdf_count=len(pdf_paths), sample_seconds=SAMPLE_SECONDS,
              desktop=str(desktop), launch_method="os.startfile (default PDF handler)")
        for index, filename in enumerate(pdf_paths, 1):
            path = Path(filename)
            event(log, "pdf_selected", pdf_index=index, path=str(path),
                  size_bytes=path.stat().st_size if path.is_file() else None)
            before = {p.pid for p in adobe_processes(psutil)}
            start = time.perf_counter()
            try:
                os.startfile(str(path))
                event(log, "launch_request_returned", pdf_index=index,
                      request_duration_s=round(time.perf_counter() - start, 3),
                      note="This is not a PDF render-complete measurement.")
            except Exception as exc:
                event(log, "launch_error", pdf_index=index, error=repr(exc))
                continue

            seen = set()
            end = start + SAMPLE_SECONDS
            while time.perf_counter() < end:
                elapsed = time.perf_counter() - start
                procs = adobe_processes(psutil)
                current = {p.pid for p in procs}
                new = current - before - seen
                for pid in sorted(new):
                    event(log, "adobe_process_observed", pdf_index=index, pid=pid,
                          elapsed_s=round(elapsed, 2))
                seen.update(current)
                if not procs and elapsed < 2:
                    event(log, "no_adobe_process_observed_yet", pdf_index=index,
                          note="Default PDF handler may not be Adobe.")
                for proc in procs:
                    try:
                        writer.writerow(sample_process(psutil, proc, index, path.name, elapsed))
                    except (psutil.Error, OSError, ValueError) as exc:
                        event(log, "sample_error", pdf_index=index, pid=proc.pid,
                              error=repr(exc))
                csv_file.flush()
                time.sleep(SAMPLE_INTERVAL)
            event(log, "pdf_monitoring_complete", pdf_index=index,
                  observed_adobe_pids=sorted(seen), elapsed_s=round(time.perf_counter() - start, 2))
        event(log, "session_complete")

    messagebox.showinfo("Adobe PDF diagnostic complete",
                        "Logs saved to:\n" + str(log_path) + "\n" + str(csv_path))
    root.destroy()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        details = traceback.format_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Diagnostic error", details[-3000:])
            root.destroy()
        except Exception:
            print(details, file=sys.stderr)
        raise
