"""
AutoCAD · Inventor → PDF  (Silent Batch Printer — Combined)
============================================================
Accepts any mix of AutoCAD DWGs, Inventor IDWs, and Inventor-exported DWGs.
Each file is automatically routed to the correct export engine:

  • Inventor IDW / Inventor-exported DWG → Inventor PDF Translator Add-in
  • AutoCAD-native DWG                   → AutoCAD DWG To PDF.pc3 plotter

Detection is done by binary-sniffing the first 64 KB of every .dwg file:
Inventor always embeds b"Autodesk Inventor" in that region; AutoCAD never does.

Key behaviours
--------------
  • Single multi-page PDF per Inventor drawing (all sheets).
  • One PDF per paper-space layout per AutoCAD drawing
    (single layout → named after the drawing; multi-layout → Drawing - Layout.pdf).
  • PDFs saved into a "PDF Temp Copies" subfolder inside each drawing's folder.
  • Full combined log on the Desktop: "AutoCAD-INVENTOR DWG to PDF Log.txt"
  • Explorer opens every output folder on completion.

Usage (pick any)
-----------------
  1. Drag-and-drop .idw / .dwg files onto this script (or a shortcut)
  2. Right-click selected files → Send To → AutoCAD-INVENTOR DWG to PDF
  3. Run with no args — a file-picker dialog opens
  4. python "AutoCAD-INVENTOR_DWG to PDF.py" file1.idw file2.dwg ...

Requirements
-------------
  Inventor 2016+ with PDF Translator Add-in  (for Inventor / Inventor-DWG files)
  AutoCAD  2016+ with "DWG To PDF.pc3"        (for AutoCAD-native DWG files)
  cscript.exe  (built into Windows — no install needed)
"""

import sys
import os

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
_EMERGENCY_LOG = os.path.join(os.path.expanduser("~"), "Desktop",
                              "AutoCAD-INVENTOR DWG to PDF CRASH.txt")
try:
    import datetime
    import traceback
    import subprocess
    import tempfile
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from pathlib import Path
except Exception as _ie:
    _msg = f"STARTUP FAILED\n\nError: {_ie}\n"
    try:
        with open(_EMERGENCY_LOG, "w", encoding="utf-8") as _f:
            _f.write(_msg)
    except Exception:
        pass
    try:
        import tkinter, tkinter.messagebox as _mb
        _r = tkinter.Tk(); _r.withdraw()
        _mb.showerror("DWG to PDF — Startup Error", _msg)
        _r.destroy()
    except Exception:
        input(_msg + "\nPress Enter to close...")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PDF_SUBFOLDER      = "PDF Temp Copies"   # set "" to save alongside drawings
PDF_PLOTTER        = "DWG To PDF.pc3"    # AutoCAD plotter (ships with every AutoCAD)
VECTOR_RESOLUTION  = 200                 # DPI for Inventor PDF export
COLOR_MODE         = 0                   # 0 = colour, 1 = black & white

LOG_PATH = os.path.join(os.path.expanduser("~"), "Desktop",
                        "AutoCAD-INVENTOR DWG to PDF Log.txt")


# ---------------------------------------------------------------------------
# Routing — binary sniff
# ---------------------------------------------------------------------------

def _is_inventor_dwg(path: str) -> bool:
    """Return True if *path* is a DWG saved by Autodesk Inventor.

    Inventor embeds b'Autodesk Inventor' in the first 64 KB of every DWG it
    saves.  AutoCAD-native DWGs never contain this string.
    """
    try:
        with open(path, "rb") as fh:
            blob = fh.read(65536)
        return b"Autodesk Inventor" in blob
    except Exception:
        return False


# ---------------------------------------------------------------------------
# VBScript — Inventor path
# ---------------------------------------------------------------------------
_VBS_INVENTOR = r"""
Option Explicit

Dim fso, f, i
Set fso = CreateObject("Scripting.FileSystemObject")

Dim sJobsPath : sJobsPath  = WScript.Arguments(0)
Dim iVecRes   : iVecRes    = CInt(WScript.Arguments(1))
Dim iColorMode: iColorMode = CInt(WScript.Arguments(2))

Set f = fso.OpenTextFile(sJobsPath, 1)
Dim jobs() : ReDim jobs(0)
Dim nJobs  : nJobs = 0
Do While Not f.AtEndOfStream
    ReDim Preserve jobs(nJobs)
    jobs(nJobs) = f.ReadLine()
    nJobs = nJobs + 1
Loop
f.Close

' ── Connect to Inventor (always fresh hidden instance) ───────────────────────
Dim oInv
On Error Resume Next
Set oInv = CreateObject("Inventor.Application")
If Err.Number <> 0 Then
    WScript.Echo "FATAL:Could not start Inventor: " & Err.Description
    WScript.Quit 1
End If
On Error GoTo 0

oInv.Visible = False
oInv.SilentOperation = True
WScript.Echo "STATUS:LAUNCHED"

WScript.Sleep 3000

' ── Locate PDF translator add-in ─────────────────────────────────────────────
Dim oPDF, sAddInId
sAddInId = "{0AC6FD96-2F4D-42CE-8BE0-8AEA580399E4}"

Dim k
On Error Resume Next
Set oPDF = oInv.ApplicationAddIns.ItemById(sAddInId)
If Err.Number <> 0 Or IsNull(oPDF) Or IsEmpty(oPDF) Then
    Err.Clear
    Dim sAppList : sAppList = ""
    For k = 1 To oInv.ApplicationAddIns.Count
        Dim sAN : sAN = oInv.ApplicationAddIns.Item(k).DisplayName
        sAppList = sAppList & " | " & sAN
        If (InStr(UCase(sAN), "PDF") > 0 Or InStr(UCase(sAN), "DWG") > 0) _
           And (IsNull(oPDF) Or IsEmpty(oPDF)) Then
            Set oPDF = oInv.ApplicationAddIns.Item(k)
        End If
    Next
    If Len(sAppList) = 0 Then sAppList = " (none)"
    WScript.Echo "STATUS:ADDINLIST:" & sAppList
End If

If Err.Number = 0 And Not IsNull(oPDF) And Not IsEmpty(oPDF) Then
    If Not oPDF.Activated Then
        oPDF.Activate
        WScript.Sleep 2000
    End If
End If
Err.Clear
On Error GoTo 0

If IsNull(oPDF) Or IsEmpty(oPDF) Then
    WScript.Echo "FATAL:PDF translator add-in not found." & _
        " Open Inventor -> Tools -> Add-Ins and confirm the PDF add-in is listed."
    oInv.SilentOperation = False
    oInv.Quit
    WScript.Quit 1
End If
WScript.Echo "STATUS:ADDIN:" & oPDF.DisplayName

' ── Process each drawing ─────────────────────────────────────────────────────
Dim sLine, nPipe, sDrawPath, sPdfPath, oDoc, oCtx, oOpts, oData, bOpenOK

For i = 0 To nJobs - 1
    sLine = Trim(jobs(i))
    If Len(sLine) > 0 Then
        nPipe = InStr(sLine, "|")
        If nPipe > 0 Then
            sDrawPath = Left(sLine, nPipe - 1)
            sPdfPath  = Mid(sLine, nPipe + 1)

            WScript.Echo "OPENING:" & sDrawPath

            bOpenOK = False
            On Error Resume Next
            Set oDoc = oInv.Documents.Open(sDrawPath, False)
            If Err.Number <> 0 Then
                WScript.Echo "FAIL:" & sDrawPath & "|Open failed: " & Err.Description
                Err.Clear
            Else
                bOpenOK = True
                WScript.Echo "OPENED"
            End If
            On Error GoTo 0

            If bOpenOK Then
                WScript.Echo "EXPORTING"
                On Error Resume Next

                oDoc.Activate

                Set oCtx  = oInv.TransientObjects.CreateTranslationContext()
                oCtx.Type = 13059   ' kFileBrowseIOMechanism

                Set oOpts = oInv.TransientObjects.CreateNameValueMap()
                Set oData = oInv.TransientObjects.CreateDataMedium()
                oData.FileName = sPdfPath

                oPDF.HasSaveCopyAsOptions oDoc, oCtx, oOpts
                Err.Clear

                oOpts.Value("Sheet_Range")        = 14082  ' kPrintAllSheets
                oOpts.Value("Vector_Resolution")  = iVecRes
                oOpts.Value("All_Color_AS_Black") = (iColorMode <> 0)

                oPDF.SaveCopyAs oDoc, oCtx, oOpts, oData

                If Err.Number <> 0 Then
                    WScript.Echo "FAIL:" & sDrawPath & "|Export failed: [" & Err.Number & "] " & _
                                 Err.Description & " (Source: " & Err.Source & ")"
                    Err.Clear
                ElseIf fso.FileExists(sPdfPath) Then
                    WScript.Echo "DONE:" & sPdfPath
                Else
                    WScript.Echo "FAIL:" & sDrawPath & "|SaveCopyAs returned OK but no PDF was created."
                End If

                oDoc.Close True
                Err.Clear
                On Error GoTo 0
            End If
        End If
    End If
Next

oInv.SilentOperation = False
oInv.Quit
WScript.Echo "STATUS:QUIT"
WScript.Echo "STATUS:FINISHED"
"""


# ---------------------------------------------------------------------------
# VBScript — AutoCAD path
# ---------------------------------------------------------------------------
_VBS_ACAD = r"""
Option Explicit

Dim fso, f, i
Set fso = CreateObject("Scripting.FileSystemObject")

Dim sJobsPath  : sJobsPath   = WScript.Arguments(0)
Dim sPdfPlotter: sPdfPlotter = WScript.Arguments(1)

Set f = fso.OpenTextFile(sJobsPath, 1)
Dim jobs() : ReDim jobs(0)
Dim nJobs  : nJobs = 0
Do While Not f.AtEndOfStream
    ReDim Preserve jobs(nJobs)
    jobs(nJobs) = f.ReadLine()
    nJobs = nJobs + 1
Loop
f.Close

' ── Connect to AutoCAD ───────────────────────────────────────────────────────
' IMPORTANT: Use GetObject to attach to the RUNNING AutoCAD instance first.
' A hidden CreateObject instance does not inherit the user's network drive
' mappings, so Documents.Open fails with "remote server machine unavailable"
' for any file on a mapped or UNC path.
' Fall back to CreateObject only when AutoCAD is not already running.
Dim oAcad, bLaunched
bLaunched = False

On Error Resume Next
Set oAcad = GetObject(, "AutoCAD.Application")
If Err.Number <> 0 Then
    Err.Clear
    Set oAcad = CreateObject("AutoCAD.Application")
    If Err.Number <> 0 Then
        WScript.Echo "FATAL:Could not start AutoCAD: " & Err.Description
        WScript.Quit 1
    End If
    ' Keep Visible=True but minimise — hidden COM servers can't access
    ' mapped network drives on some Windows/AutoCAD configurations.
    ' Minimised gives full user-session network access; closes when done.
    oAcad.Visible = True
    oAcad.WindowState = 2   ' acMin — minimised to taskbar
    bLaunched = True
    WScript.Echo "STATUS:LAUNCHED"
Else
    WScript.Echo "STATUS:ATTACHED"
End If
On Error GoTo 0

' ── CRITICAL: disable background plotting ────────────────────────────────────
' BACKGROUNDPLOT=1 queues jobs asynchronously — PlotToFile returns before the
' file exists, producing E_FAIL (-2147467259).  Set to 0 for synchronous plot.
On Error Resume Next
oAcad.SetSystemVariable "BACKGROUNDPLOT", 0
Err.Clear
On Error GoTo 0

' ── Process each drawing ─────────────────────────────────────────────────────
Dim sLine, nPipe, sDrawPath, sPdfBase, oDoc, bOpenOK

For i = 0 To nJobs - 1
    sLine = Trim(jobs(i))
    If Len(sLine) > 0 Then
        nPipe = InStr(sLine, "|")
        If nPipe > 0 Then
            sDrawPath = Left(sLine, nPipe - 1)
            sPdfBase  = Mid(sLine, nPipe + 1)

            WScript.Echo "OPENING:" & sDrawPath

            bOpenOK = False
            On Error Resume Next
            Set oDoc = oAcad.Documents.Open(sDrawPath, True)
            If Err.Number <> 0 Then
                WScript.Echo "FAIL:" & sDrawPath & "|Open failed: " & Err.Description
                Err.Clear
            Else
                bOpenOK = True
            End If
            On Error GoTo 0

            If bOpenOK Then
                Dim oLayouts : Set oLayouts = oDoc.Layouts
                Dim nPaper   : nPaper = 0
                Dim oLay
                For Each oLay In oLayouts
                    If UCase(oLay.Name) <> "MODEL" Then nPaper = nPaper + 1
                Next
                WScript.Echo "OPENED:" & nPaper

                If nPaper = 0 Then
                    WScript.Echo "FAIL:" & sDrawPath & "|No paper-space layouts found."
                Else
                    On Error Resume Next

                    For Each oLay In oLayouts
                        If UCase(oLay.Name) <> "MODEL" Then
                            oDoc.ActiveLayout = oLay
                            WScript.Echo "LAYOUT:" & oLay.Name

                            Dim sPdfPath
                            If nPaper = 1 Then
                                sPdfPath = sPdfBase & ".pdf"
                            Else
                                sPdfPath = sPdfBase & " - " & oLay.Name & ".pdf"
                            End If

                            ' Re-apply BACKGROUNDPLOT=0 — AutoCAD resets it when
                            ' opening drawings that have it saved in their own settings.
                            oAcad.SetSystemVariable "BACKGROUNDPLOT", 0
                            Err.Clear

                            ' Wait for the layout regen to complete before plotting.
                            ' Drawings that open quickly haven't finished their initial
                            ' REGEN when PlotToFile is called — E_FAIL results.
                            ' An explicit Regen + brief sleep ensures it's ready.
                            oDoc.Regen 1
                            Err.Clear
                            WScript.Sleep 2000

                            ' Log the plot style so we can see if CTB/STB is missing.
                            Dim sStyle : sStyle = ""
                            On Error Resume Next
                            sStyle = oLay.StyleSheet
                            Err.Clear
                            On Error GoTo 0
                            If Len(sStyle) > 0 Then
                                WScript.Echo "STATUS:STYLE:" & sStyle
                            End If

                            ' Attempt 1: override plotter with DWG To PDF.pc3
                            Err.Clear
                            oDoc.Plot.PlotToFile sPdfPath, sPdfPlotter

                            If Err.Number <> 0 Then
                                Dim nErr1 : nErr1 = Err.Number
                                Dim sErr1 : sErr1 = Err.Description
                                Err.Clear

                                ' Attempt 2: layout's own plotter (no override)
                                WScript.Echo "STATUS:RETRY_NO_OVERRIDE:" & oLay.Name
                                oDoc.Plot.PlotToFile sPdfPath

                                If Err.Number <> 0 Then
                                    WScript.Echo "FAIL:" & sDrawPath & _
                                        "|Layout [" & oLay.Name & "] export failed (both attempts). " & _
                                        "Attempt1 [" & nErr1 & "] / Attempt2 [" & Err.Number & "]"
                                    Err.Clear
                                ElseIf fso.FileExists(sPdfPath) Then
                                    WScript.Echo "DONE:" & sPdfPath
                                Else
                                    WScript.Echo "FAIL:" & sDrawPath & _
                                        "|Layout [" & oLay.Name & "] no PDF created — " & _
                                        "set the page setup to use 'DWG To PDF.pc3' in AutoCAD."
                                End If
                            Else
                                WScript.Echo "DONE:" & sPdfPath
                            End If
                        End If
                    Next

                    Err.Clear
                    On Error GoTo 0
                End If

                On Error Resume Next
                oDoc.Close False
                Err.Clear
                On Error GoTo 0
            End If
        End If
    End If
Next

If bLaunched Then
    On Error Resume Next
    oAcad.Quit
    On Error GoTo 0
    WScript.Echo "STATUS:QUIT"
End If
WScript.Echo "STATUS:FINISHED"
"""


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
_log_lines = []

def log(msg: str):
    ts   = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    _log_lines.append(line)

def flush_log():
    try:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(_log_lines) + "\n")
    except Exception as e:
        print(f"  (could not write log: {e})", flush=True)


# ---------------------------------------------------------------------------
# VBScript runner — shared by both engines
# ---------------------------------------------------------------------------

def _run_vbs(vbs_template: str, jobs_path: str, extra_args: list,
             jobs: list, engine_tag: str,
             printed: list, failed: list):
    """Write VBScript to a temp file, run it, parse stdout into printed/failed."""

    vbs_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vbs",
                                         delete=False, encoding="utf-8") as vf:
            vbs_path = vf.name
            vf.write(vbs_template)

        cmd = ["cscript", "//nologo", vbs_path, jobs_path] + extra_args

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        current_stem = None

        for raw_line in proc.stdout:
            vline = raw_line.rstrip()
            if not vline:
                continue

            if vline.startswith("STATUS:"):
                status = vline[7:]
                if status == "LAUNCHED":
                    log(f"  [{engine_tag}] Started hidden instance.")
                elif status == "ATTACHED":
                    log(f"  [{engine_tag}] Attached to running instance.")
                elif status.startswith("ADDIN:"):
                    log(f"  [{engine_tag}] PDF add-in: {status[6:]}")
                elif status.startswith("ADDINLIST:"):
                    log(f"  [{engine_tag}] Add-ins:{status[10:]}")
                elif status == "QUIT":
                    log(f"  [{engine_tag}] Instance closed.")
                elif status == "FINISHED":
                    log(f"  [{engine_tag}] Export process complete.")

            elif vline.startswith("FATAL:"):
                log(f"\n  [{engine_tag}] FATAL: {vline[6:]}")
                failed.append(vline[6:])

            elif vline.startswith("OPENING:"):
                draw_path    = vline[8:]
                current_stem = Path(draw_path).stem
                # Find 1-based index in the full job list
                idx = next((j+1 for j, (d, _, __) in enumerate(jobs)
                            if d == draw_path), "?")
                log(f"\n[{idx}/{len(jobs)}] {current_stem}  [{engine_tag}]")
                log(f"  Opening ...")

            elif vline.startswith("OPENED:"):
                val = vline[7:]
                if val == "":         # Inventor just sends "OPENED" with no count
                    log(f"  Opened OK")
                else:
                    log(f"  Opened OK  ({val} paper layout(s))")

            elif vline == "OPENED":
                log(f"  Opened OK")

            elif vline == "EXPORTING":
                log(f"  Exporting to PDF ...")

            elif vline.startswith("LAYOUT:"):
                log(f"  Exporting layout: {vline[7:]} ...")

            elif vline.startswith("STATUS:STYLE:"):
                log(f"    [plot style: {vline[13:]}]")

            elif vline.startswith("STATUS:RETRY_NO_OVERRIDE:"):
                log(f"    ↳ DWG To PDF paper-size mismatch — retrying with layout's own plotter ...")

            elif vline.startswith("DONE:"):
                pdf = vline[5:]
                log(f"  → {Path(pdf).name}")
                printed.append(pdf)

            elif vline.startswith("FAIL:"):
                parts = vline[5:].split("|", 1)
                err   = parts[1] if len(parts) > 1 else "unknown error"
                stem  = Path(parts[0]).stem if parts[0] else (current_stem or "?")
                log(f"  ERROR: {err}")
                failed.append(f"{stem}  ({err})")

            else:
                log(f"  [vbs] {vline}")

        proc.wait()
        rc = proc.returncode
        if rc not in (0, None):
            log(f"  [{engine_tag}] VBScript exited with code {rc}")

    finally:
        if vbs_path:
            try:
                os.unlink(vbs_path)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    _t_start = datetime.datetime.now()
    log("=" * 60)
    log("AutoCAD · Inventor → PDF  (Silent Batch Printer)")
    log("=" * 60)

    drawing_paths = collect_drawing_paths()
    if not drawing_paths:
        log("No drawings selected — exiting.")
        flush_log()
        return

    drawing_paths = sorted(drawing_paths, key=lambda p: Path(p).stem.upper())

    # ── Route each file ──────────────────────────────────────────────────────
    # Inventor: .idw, or .dwg with Inventor binary signature
    # AutoCAD:  .dwg without Inventor signature
    inv_paths  = []
    acad_paths = []

    for p in drawing_paths:
        suffix = Path(p).suffix.lower()
        if suffix == ".idw" or _is_inventor_dwg(p):
            inv_paths.append(p)
        else:
            acad_paths.append(p)

    # ── Header summary ───────────────────────────────────────────────────────
    log(f"\n{len(drawing_paths)} drawing(s) selected:")
    for p in drawing_paths:
        tag = "Inventor" if p in inv_paths else "AutoCAD"
        log(f"  {Path(p).stem}  [{tag}]")
    log(f"\n  PDF subfolder : {PDF_SUBFOLDER or '(same as drawing)'}")
    log(f"  PDF plotter   : {PDF_PLOTTER}  (AutoCAD only)")
    log(f"  Resolution    : {VECTOR_RESOLUTION} DPI  (Inventor only)")
    log(f"  Colour mode   : {'Black & White' if COLOR_MODE else 'Colour'}  (Inventor only)")

    # ── Build combined job list (for index display) ──────────────────────────
    # jobs list mirrors drawing_paths order so [n/total] numbering is global
    all_jobs = []
    for p in drawing_paths:
        suffix      = Path(p).suffix.lower()
        draw_folder = str(Path(p).parent)
        out_folder  = os.path.join(draw_folder, PDF_SUBFOLDER) if PDF_SUBFOLDER else draw_folder
        os.makedirs(out_folder, exist_ok=True)
        stem        = Path(p).stem
        # Inventor → single PDF path;  AutoCAD → base path (no .pdf yet)
        if p in inv_paths:
            pdf_dest = os.path.join(out_folder, stem + ".pdf")
        else:
            pdf_dest = os.path.join(out_folder, stem)   # .pdf appended by VBScript
        all_jobs.append((p, pdf_dest, out_folder))

    printed     = []
    failed      = []
    out_folders = []

    # ── Inventor pass ────────────────────────────────────────────────────────
    if inv_paths:
        log(f"\n{'─'*60}")
        log(f"Inventor pass  ({len(inv_paths)} drawing(s))")
        log(f"{'─'*60}")

        jobs_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                             delete=False, encoding="utf-8") as jf:
                jobs_path = jf.name
                for p in inv_paths:
                    _, pdf_dest, _ = next(j for j in all_jobs if j[0] == p)
                    jf.write(f"{p}|{pdf_dest}\n")

            _run_vbs(_VBS_INVENTOR, jobs_path,
                     [str(VECTOR_RESOLUTION), str(COLOR_MODE)],
                     all_jobs, "Inventor", printed, failed)
        finally:
            if jobs_path:
                try:
                    os.unlink(jobs_path)
                except Exception:
                    pass

    # ── AutoCAD pass ─────────────────────────────────────────────────────────
    if acad_paths:
        log(f"\n{'─'*60}")
        log(f"AutoCAD pass  ({len(acad_paths)} drawing(s))")
        log(f"{'─'*60}")

        jobs_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                             delete=False, encoding="utf-8") as jf:
                jobs_path = jf.name
                for p in acad_paths:
                    _, pdf_dest, _ = next(j for j in all_jobs if j[0] == p)
                    jf.write(f"{p}|{pdf_dest}\n")

            _run_vbs(_VBS_ACAD, jobs_path,
                     [PDF_PLOTTER],
                     all_jobs, "AutoCAD", printed, failed)
        finally:
            if jobs_path:
                try:
                    os.unlink(jobs_path)
                except Exception:
                    pass

    # ── Summary ──────────────────────────────────────────────────────────────
    elapsed    = datetime.datetime.now() - _t_start
    total_secs = int(elapsed.total_seconds())
    mins, secs = divmod(total_secs, 60)
    time_str   = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
    per_dwg    = (f"  ({total_secs // max(len(printed), 1)}s / PDF)"
                  if printed else "")

    log("")
    log("=" * 60)
    log(f"DONE   Exported: {len(printed)}   Failed: {len(failed)}")
    for p in printed:
        log(f"  OK    {p}")
        of = str(Path(p).parent)
        if of not in out_folders:
            out_folders.append(of)
    for item in failed:
        log(f"  FAIL  {item}")
    log(f"Time taken: {time_str}{per_dwg}")
    log(f"Log saved to: {LOG_PATH}")
    flush_log()

    # Open output folders in Explorer
    for folder in out_folders:
        try:
            subprocess.Popen(["explorer.exe", folder])
        except Exception:
            pass

    summary = (
        f"Exported : {len(printed)}\n"
        f"Failed   : {len(failed)}\n"
        f"Time     : {time_str}{per_dwg}\n"
    )
    if inv_paths:
        summary += f"\n  Inventor drawings : {len(inv_paths)}"
    if acad_paths:
        summary += f"\n  AutoCAD drawings  : {len(acad_paths)}"
    if failed:
        summary += "\n\nFailed:\n" + "\n".join(f"  • {f}" for f in failed)
    summary += f"\n\nLog: {LOG_PATH}"
    messagebox.showinfo("AutoCAD · Inventor → PDF — Complete", summary)


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------

def collect_drawing_paths():
    args = [a for a in sys.argv[1:]
            if a.lower().endswith((".dwg", ".dxf", ".idw"))]
    if args:
        return args

    root = tk.Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(
        title="Select drawings to export to PDF  (IDW, DWG — AutoCAD or Inventor)",
        filetypes=[("Drawings", "*.idw *.dwg *.dxf"), ("All files", "*.*")]
    )
    root.destroy()
    return list(paths)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = f"FATAL: {e}\n{traceback.format_exc()}"
        print(msg, flush=True)
        try:
            _log_lines.append(msg)
            flush_log()
        except Exception:
            pass
        try:
            messagebox.showerror("AutoCAD · Inventor → PDF — Fatal Error",
                                 f"{e}\n\nSee log:\n{LOG_PATH}")
        except Exception:
            input("Press Enter to close...")
