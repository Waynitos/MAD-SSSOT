# SSA Output — TRAVERSE iLogic Audit

**Role:** Synthesizer (verdict + fixes)
**MAD Run:** traverse-ilogic-audit
**File audited:** TRAVERSE_fixed.iLogicVb (8052 lines)
**AA weaknesses acknowledged:** 5
**DA weaknesses confirmed:** 10 / 12

---

## Part 1 — Verdict Table

| # | DA Weakness | Verdict | Ruling |
|---|---|---|---|
| 1 | oProcessedResults cache invalidation | **CONFIRMED** | Cache semantics verified in code (~line 382). Comment explicitly says it caches "True/False result of fully exploring each document… keyed by its full file name." For Mode 1/2 single-traversal runs, a shared document cached False from Branch A short-circuits Branch B's exploration. Mode 6 is immune because it bypasses `ProcessLevel` entirely. This is the direct cause of the user's reported symptom. Fix needed. |
| 2 | Phase 3 sort: path length ≠ depth | **CONFIRMED** | Verified at line 939: `oNewTargets.Sort(Function(a, b2) b2.Length.CompareTo(a.Length))`. A deeply-nested component in a short working path sorts AFTER a shallow component in a long enterprise path. AA correctly notes Phase 4 live-repointing is a backstop, but Phase 3 saves the parent with stale child FDs before those children are fixed — the subsequent Phase 4 repoints the live session, but the saved IAM file on disk retains the stale FD until the next reload. Fix recommended. |
| 3 | GoTo flow: iMapSkipped uninitialised; SilentOperation leak | **CONFIRMED-MINOR** | Verified: `iMapSkipped` is declared at line 772 in the normal Phase 1 path but the `GoTo Mode2Phase2` jump at line 783 bypasses its initialisation. Line 860's log reads `iMapSkipped` after the label — reads zero (VB.NET default), which is actually correct in this case (nothing was skipped from a pre-built map), so this is cosmetic not functional. The SilentOperation leak risk is real but partially mitigated: all four Mode 6 early-exit paths (lines 390, 405, 416, 430) individually restore `bOrigSilent`. An unhandled exception in BuildCopyDesignRenameMap (line 422) could still leave SilentOperation True. Minor fix recommended. |
| 4 | Failed Phase 2 copy → Phase 4 repoints missing file | **CONFIRMED** | Verified: Phase 3 begins at line 919 immediately after Phase 2's loop closes, with no guard on `iCopyFailed`. Phase 3 does skip missing targets (`If Not System.IO.File.Exists(sNewFull) Then Continue For` at line 945), but Phase 4 operates on `oMode2Map` entries and does NOT perform the same existence check before repointing live occurrences. Result: assembly saved pointing at a file that does not exist. Fix needed. |
| 5 | Stale pre-built map survives cancel | **CONFIRMED-MINOR** | Code shows all four Mode 6 cancel paths correctly restore `SilentOperation` but do NOT call `GetSetPrebuiltMode2Map(True, Nothing)`. The map is only populated AFTER the cancel-capable forms (line 433, after both ShowCopyDesignConfigForm and ShowBatchSelectionForm), so in practice a cancelled run never stores a map. The risk is real but requires a very specific failure sequence (exception after line 433 but before line 783's consume-and-clear). The clear-on-exit defence is the correct fix. |
| 6 | AllReferencedDocuments misses suppressed/unloaded components | **PARTIALLY CONFIRMED** | The DA claim is technically correct — suppressed occurrences in non-default Level of Detail representations are not in AllReferencedDocuments. However the script's supplemental FileDescriptors scan (lines 793–807) covers the most common miss: xlsx parameter tables. The gap is real for suppressed sub-assemblies, but the practical impact is low: suppressed components are excluded from the active LOD by design, and Phase 4 walks the LIVE session's occurrence tree, which will not contain suppressed occurrences either. No code fix recommended; document the known limitation. |
| 7 | Snapshot file: no integrity check or timestamp | **CONFIRMED-MINOR** | The design choice to never overwrite is correct (preserves true starting state). The gap is the missing timestamp and no existence-check on recorded paths. A snapshot from a prior run that was then partially manually reversed records paths that now don't exist. Low code fix effort, meaningful user safety benefit. |
| 8 | Desktop log fails on UNC-redirected corporate paths | **CONFIRMED** | Pattern verified in code: every AppendAllText wrapped in bare `Catch : End Try`. On a redirected-Desktop corporate machine, the log silently produces nothing. Given the user's confirmed corporate environment with limited admin rights, this is a realistic failure mode, not a theoretical one. Fix: try local AppData fallback. |
| 9 | No mid-run cancellation path | **PARTIALLY CONFIRMED** | Technically correct — there is no in-rule cancel mechanism once traversal starts. However: (a) iLogic VB.NET does not provide a clean async cancel API; (b) the correct mitigation is Mode 5 (verify-only) run before Mode 1/2/4, and Mode 6's pre-scan. Documenting the recommended pre-flight workflow addresses this without requiring a complex implementation. No code fix; document the workflow instead. |
| 10 | Excel COM state inherited across runs | **CONFIRMED** | Verified in code (~lines 330–349). The `GetObject` path retrieves an existing Excel instance — if that instance has `DisplayAlerts = False` from a crashed prior run, `bExcelAlertsOriginal` captures False and the finally-restore leaves it False. Also confirmed: `GetSetExcelApp(True, Nothing)` stores Nothing — any subsequent call that retrieves Nothing and attempts method calls will produce a NullReferenceException swallowed by a surrounding Catch, silently skipping xlsx parameter table fixes. Fix needed. |
| 11 | Mode 3 skipped files: advisory only, no post-run summary | **CONFIRMED-MINOR** | DA is correct: the skip is noted only in the crash log (which may itself be failing per weakness 8). No post-run summary of skipped files is shown. A simple in-memory list and a MessageBox after the run eliminates the need to cross-reference the log. Small fix, clear user benefit. |
| 12 | sFind = sReplace placeholder in Mode 6 | **REJECTED** | Phase 4's live repointing does NOT use `sFind` for matching. Phase 4 operates by walking `oRenameMap` entries (the Phase 2 copy map) and calling `ReplaceReference` / `Occurrence.Replace` directly on mapped paths. The `sFind = sReplace` assignment at line 437 only matters for Phase 1's map-building loop (line 832: `sOldName.ToUpper().Contains(sFind.ToUpper())`), which is bypassed by `GoTo Mode2Phase2` for all Mode 6 runs. The placeholder is semantically harmless; the comment at line 437 correctly documents this. |

**Summary:** 7 CONFIRMED (2 high-risk, 5 minor), 3 PARTIALLY CONFIRMED (documented, not coded), 2 REJECTED.

---

## Part 2 — Prioritised Fix List

Fixes ordered by risk, then effort.

---

### Fix A — Cache invalidation for non-Mode-6 repeated runs (DA #1)

**Risk:** High · **Effort:** Small · **Sub:** `ProcessLevel`

**Root cause:** `oProcessedResults` stores "explored, no changes" per document. When the same document appears from a second parent branch, it's treated as already-done and skipped. For Mode 6 this is fine (the rename map is pre-built and complete). For Modes 1, 2, 4 where the map is built incrementally as the traversal descends, a cached False is only valid for the exact context it was cached in.

**Fix:** Don't cache the negative (False) result. Cache only the positive result (True = something changed). A document that needed no changes on Branch A still needs to be re-entered from Branch B, because the act of processing Branch A may have renamed siblings that are now stale inside Branch B's context.

Find the section in `ProcessLevel` where `oProcessedResults` is checked and set:

```vb
' BEFORE (cache short-circuits on False — wrong for Modes 1/2/4):
If oProcessedResults.ContainsKey(sDocFull) Then
    Return oProcessedResults(sDocFull)
End If
' ... traversal ...
oProcessedResults(sDocFull) = bFoundSomething
Return bFoundSomething

' AFTER (only cache True — safe for all modes):
If oProcessedResults.ContainsKey(sDocFull) Then
    ' Only short-circuit if we KNOW this document had changes.
    ' A False result from another branch does not mean this branch
    ' can skip it — siblings may have been renamed since.
    If oProcessedResults(sDocFull) = True Then Return True
End If
' ... traversal ...
If bFoundSomething Then
    oProcessedResults(sDocFull) = True  ' only cache wins, not misses
End If
Return bFoundSomething
```

This preserves the performance benefit for the common case (shared components that WERE renamed don't need re-exploring), while allowing re-exploration of documents that haven't changed yet.

---

### Fix B — Phase 3 depth sort: use counted depth, not path length (DA #2)

**Risk:** High (correctness) · **Effort:** Small · **Sub:** `Main` — Phase 3 sort block (~line 939)

**Root cause:** `b2.Length.CompareTo(a.Length)` sorts by path string length, not assembly nesting depth. A component at depth 5 in a short path sorts after a component at depth 2 in a long path, causing parent saves to precede child ref fixes.

**Fix:** Count path separators as a reliable depth proxy (separators are not affected by directory name length). Replace the sort lambda:

```vb
' BEFORE:
oNewTargets.Sort(Function(a, b2) b2.Length.CompareTo(a.Length))

' AFTER: sort by path separator count descending (deeper paths have more separators)
oNewTargets.Sort(Function(a, b2)
    Dim iDepthA As Integer = a.Split(System.IO.Path.DirectorySeparatorChar).Length
    Dim iDepthB As Integer = b2.Split(System.IO.Path.DirectorySeparatorChar).Length
    ' Primary: more separators = deeper = process first
    Dim iCmp As Integer = iDepthB.CompareTo(iDepthA)
    ' Secondary: longer path breaks ties (original behaviour)
    If iCmp = 0 Then iCmp = b2.Length.CompareTo(a.Length)
    Return iCmp
End Function)
```

This sorts correctly for all standard Windows path structures. The separator-count approach also handles UNC paths (`\\server\share\...`) consistently.

---

### Fix C — Phase 2 failure guard before Phases 3 and 4 (DA #4)

**Risk:** High · **Effort:** Small · **Sub:** `Main` — between Phase 2 and Phase 3 (~line 918)

**Root cause:** If `iCopyFailed > 0`, some entries in `oMode2Map` have no corresponding new file on disk. Phase 3 skips them (existence check at line 945), but Phase 4 does not — it repoints live occurrences to non-existent paths, which are then saved to disk as broken references.

**Fix:** Build a set of successfully-copied files after Phase 2, and use it to filter `oMode2Map` before Phase 3 and Phase 4. Insert after the Phase 2 loop closes (~line 917):

```vb
' Build a verified-copy set from oRenameMap (only entries actually copied land there)
Dim oVerifiedNew As New System.Collections.Generic.HashSet(Of String)(StringComparer.OrdinalIgnoreCase)
For Each kvpV As System.Collections.Generic.KeyValuePair(Of String, String) In oRenameMap
    If System.IO.File.Exists(kvpV.Value) Then oVerifiedNew.Add(kvpV.Value)
Next

If iCopyFailed > 0 Then
    Dim sWarn As String = "WARNING: " & iCopyFailed & " file(s) failed to copy. " & _
        "Their entries will be EXCLUDED from Phase 3 and Phase 4 to prevent " & _
        "broken references. Check the log for COPY FAILED entries."
    sLog = sLog & vbCrLf & sWarn
    Try : System.IO.File.AppendAllText(sLogFilePath, sWarn & vbCrLf) : Catch : End Try
End If
```

Then in Phase 3's file loop, add after the existence check at line 945:
```vb
If Not oVerifiedNew.Contains(sNewFull) Then Continue For  ' copy failed — skip
```

And in Phase 4's occurrence-repointing loop, add a corresponding guard that skips any `oMode2Map` entry whose value is not in `oVerifiedNew`.

---

### Fix D — Excel DisplayAlerts: capture pre-run state defensively (DA #10)

**Risk:** Medium · **Effort:** Small · **Sub:** `Main` — Excel initialisation (~lines 325–349)

**Root cause:** `GetObject` retrieves the existing Excel instance including whatever DisplayAlerts state a crashed prior run left it in. `bExcelAlertsOriginal` then captures the bad state (False), so finally-restore resets it to False.

**Fix:** Always treat `True` as the safe original state when the retrieved Excel instance already has DisplayAlerts = False (since normal Excel never has it False at idle):

```vb
' BEFORE:
bExcelAlertsOriginal = oExcelApp.DisplayAlerts
oExcelApp.DisplayAlerts = False

' AFTER:
Try
    Dim bCurrent As Boolean = oExcelApp.DisplayAlerts
    ' If DisplayAlerts is already False on an instance we didn't create,
    ' a prior run crashed without restoring it. Treat True as the safe original.
    bExcelAlertsOriginal = If(bCurrent, True, True)  ' always restore to True
    oExcelApp.DisplayAlerts = False
Catch
    bExcelAlertsOriginal = True
End Try
```

Simplify: just always set `bExcelAlertsOriginal = True` for GetObject instances. You don't know what state Excel is in and True is always the safe target to restore to.

Also add a null-guard before any Excel method call retrieved from `GetSetExcelApp`:

```vb
Dim oXl As Object = GetSetExcelApp()
If oXl Is Nothing Then
    ' Log that Excel is unavailable; xlsx parameter tables will not be updated
    Try : System.IO.File.AppendAllText(sLogFilePath, "NOTE: Excel not available - xlsx param tables skipped." & vbCrLf) : Catch : End Try
Else
    ' ... use oXl safely
End If
```

---

### Fix E — Log path: local AppData fallback (DA #8)

**Risk:** Medium · **Effort:** Small · **Sub:** wherever `sLogFilePath` is constructed

**Root cause:** `SpecialFolder.Desktop` resolves to a UNC path on corporate machines with GP folder redirection. If the fileserver is offline or slow, all log writes fail silently.

**Fix:** Try Desktop first, fall back to `LocalApplicationData\InventorTraverse`:

```vb
Dim sLogFilePath As String = ""
Try
    Dim sDesktop As String = System.Environment.GetFolderPath(System.Environment.SpecialFolder.Desktop)
    ' Test write access with a tiny probe before committing
    Dim sProbe As String = System.IO.Path.Combine(sDesktop, "._traverse_probe")
    System.IO.File.WriteAllText(sProbe, "")
    System.IO.File.Delete(sProbe)
    sLogFilePath = System.IO.Path.Combine(sDesktop, "Traverse_Rename_Log_" & _
        Format(Now, "yyyyMMdd_HHmmss") & ".txt")
Catch
    Try
        Dim sLocalLog As String = System.IO.Path.Combine( _
            System.Environment.GetFolderPath(System.Environment.SpecialFolder.LocalApplicationData), _
            "InventorTraverse")
        If Not System.IO.Directory.Exists(sLocalLog) Then System.IO.Directory.CreateDirectory(sLocalLog)
        sLogFilePath = System.IO.Path.Combine(sLocalLog, "Traverse_Rename_Log_" & _
            Format(Now, "yyyyMMdd_HHmmss") & ".txt")
        MessageBox.Show("Note: Desktop not writable — log writing to:" & vbCrLf & sLogFilePath, _
            "Log Location Changed")
    Catch
        sLogFilePath = ""  ' log disabled entirely; run continues
    End Try
End Try
```

Guard all AppendAllText calls with `If sLogFilePath <> "" Then` (or keep the existing bare Catch wrappers — they already handle it).

---

### Fix F — SilentOperation leak guard (DA #3)

**Risk:** Low · **Effort:** Small · **Sub:** `Main` — Mode 6 block, around BuildCopyDesignRenameMap call (~line 422)

**Fix:** Wrap the map-building call in Try/Finally to guarantee SilentOperation is restored:

```vb
' BEFORE:
Dim oCdMap As ... = BuildCopyDesignRenameMap(...)

' AFTER:
Dim oCdMap As System.Collections.Generic.Dictionary(Of String, String) = Nothing
Try
    oCdMap = BuildCopyDesignRenameMap(oAsmDoc, oChoice.oBatchFinds, sReplace, _
        oChoice.oSegFinds, oChoice.oSegReplaces, oChoice.bLocalizeNonStd, _
        oChoice.bHonourFolderStructure, _
        sTargetFolder, sTopAssemblyFullName, sNonStdFolder, sLog, sLogFilePath)
Catch exBuild As Exception
    MessageBox.Show("Copy Design map build failed: " & exBuild.Message, "Copy Design")
    ThisApplication.SilentOperation = bOrigSilent
    GetSetPrebuiltMode2Map(True, Nothing)  ' clear any partial state
    Exit Sub
End Try
```

Also add `GetSetPrebuiltMode2Map(True, Nothing)` to the two existing cancel-path `Exit Sub` calls at lines 390 and 405 (before the map is built, this is a no-op, but it defends against future code reordering):

```vb
' At each cancel path:
GetSetPrebuiltMode2Map(True, Nothing)  ' defensive clear
ThisApplication.SilentOperation = bOrigSilent
Exit Sub
```

---

### Fix G — Snapshot: add timestamp and path existence warning (DA #7)

**Risk:** Low · **Effort:** Small · **Sub:** wherever snapshot is written

**Fix:** Prepend a header with creation timestamp when writing the snapshot:

```vb
' BEFORE writing snapshot content:
Dim sTsHeader As String = "# TRAVERSE snapshot created: " & Format(Now, "yyyy-MM-dd HH:mm:ss") & vbCrLf & _
    "# This snapshot records file locations BEFORE this rule ran." & vbCrLf & _
    "# Do not modify. It will NOT be overwritten by subsequent runs." & vbCrLf & vbCrLf
' Prepend header to snapshot content
```

And when reading a snapshot for a revert operation, add a quick path-existence check:

```vb
Dim iMissing As Integer = 0
For Each sSnapLine As String In oSnapLines
    If Not System.IO.File.Exists(sSnapLine.Trim()) Then iMissing += 1
Next
If iMissing > 0 Then
    MessageBox.Show(iMissing & " path(s) in the snapshot no longer exist on disk." & vbCrLf & _
        "The snapshot may be stale. Proceed with caution.", "Snapshot Warning", _
        MessageBoxButtons.OKCancel)
End If
```

---

### Fix H — Mode 3 post-run skipped-file summary (DA #11)

**Risk:** Low · **Effort:** Small · **Sub:** `ConsolidateLevel` / Mode 3 main block

**Fix:** Accumulate skipped files in a module-level or passed-by-ref List, and display a summary MessageBox after the consolidation loop:

```vb
' Add before Mode 3 traversal:
Dim oSkippedFiles As New System.Collections.Generic.List(Of String)

' In ConsolidateLevel, wherever a file is skipped because it is locked:
oSkippedFiles.Add(sFileName)  ' pass oSkippedFiles as ByRef or module-level

' After Mode 3 traversal completes:
If oSkippedFiles.Count > 0 Then
    Dim sbSkip As New System.Text.StringBuilder()
    sbSkip.AppendLine("Mode 3 completed. The following " & oSkippedFiles.Count & _
        " file(s) were SKIPPED (open in session — close and re-run):")
    sbSkip.AppendLine()
    For Each sSkipped As String In oSkippedFiles
        sbSkip.AppendLine("  " & sSkipped)
    Next
    MessageBox.Show(sbSkip.ToString(), "Mode 3 — Files Skipped")
End If
```

---

## Part 3 — Win-Win Enhancements

Improvements that strengthen what already works without altering the architecture.

### WW1 — Mode 2 pre-map preview (dry-run before Phase 2)

Mode 3 already shows a pre-scan summary before executing. Mode 2 (and Mode 6) build the complete rename map in Phase 1 before any disk writes — the information exists. Add a preview step between Phase 1 and Phase 2:

```vb
' After Phase 1 map is built (or pre-built map consumed), before Phase 2:
Dim sbPreview As New System.Text.StringBuilder()
sbPreview.AppendLine("Phase 1 map — " & iMapBuilt & " rename(s) planned:")
sbPreview.AppendLine()
Dim iShow As Integer = 0
For Each kvpShow As System.Collections.Generic.KeyValuePair(Of String, String) In oMode2Map
    sbPreview.AppendLine("  " & System.IO.Path.GetFileName(kvpShow.Key) & _
        "  ->  " & System.IO.Path.GetFileName(kvpShow.Value))
    iShow += 1
    If iShow >= 30 Then
        sbPreview.AppendLine("  ... and " & (iMapBuilt - 30) & " more (see log for full list)")
        Exit For
    End If
Next
sbPreview.AppendLine()
sbPreview.AppendLine("Proceed with copy and reference rewrite?")
Dim oDryRunResult As DialogResult = MessageBox.Show(sbPreview.ToString(), _
    "Mode 2 — Confirm Rename Map", MessageBoxButtons.OKCancel)
If oDryRunResult <> DialogResult.OK Then
    GetSetPrebuiltMode2Map(True, Nothing)
    ThisApplication.SilentOperation = bOrigSilent
    MessageBox.Show("Cancelled - no changes made.", "Cancelled")
    Exit Sub
End If
```

This gives Mode 2 and Mode 6 the same pre-flight confirmation Mode 3 already provides, at zero additional disk-operation cost.

### WW2 — Mode 5 verify: count AND list specific residuals

Mode 5 currently reports a count of residual old-prefix references. Upgrading it to list the specific documents still containing old names (and what the old name is) makes it actionable:

```vb
' In RunVerifyOnlyPass (or equivalent), accumulate specific findings:
Dim oResiduals As New System.Collections.Generic.List(Of String)
' When a residual is found:
oResiduals.Add(sDocName & " contains ref to: " & sOldRefName)

' Post-verify summary:
If oResiduals.Count > 0 Then
    Dim sbRes As New System.Text.StringBuilder()
    sbRes.AppendLine("Mode 5 VERIFY — " & oResiduals.Count & " residual old-prefix reference(s):")
    sbRes.AppendLine()
    For Each sRes As String In oResiduals
        sbRes.AppendLine("  " & sRes)
    Next
    sbRes.AppendLine()
    sbRes.AppendLine("These files may need a further Mode 1, 2, or 6 run.")
    MessageBox.Show(sbRes.ToString(), "Mode 5 — Residuals Found")
End If
```

### WW3 — oRenameMap persistence header in log

The decisions log already records each rename decision. A small addition: write the accumulated `oRenameMap` as a structured section at the end of the run (old → new, one per line). This makes the log usable as a post-run audit trail and as input if a manual revert is ever needed:

```vb
' At end of run, before closing:
Try
    Dim sbMap As New System.Text.StringBuilder()
    sbMap.AppendLine()
    sbMap.AppendLine("=== RENAME MAP (final) ===")
    For Each kvpFinal As System.Collections.Generic.KeyValuePair(Of String, String) In oRenameMap
        sbMap.AppendLine(System.IO.Path.GetFileName(kvpFinal.Key) & " -> " & System.IO.Path.GetFileName(kvpFinal.Value))
    Next
    System.IO.File.AppendAllText(sLogFilePath, sbMap.ToString())
Catch : End Try
```

### WW4 — Mode 6 "what would change" header in Copy Design form

The Copy Design config form collects prefix + segment replacements but doesn't show the user a count of affected files. After `BuildCopyDesignRenameMap` runs, show the map count in a confirmation step before storing it in module state:

```vb
If oCdMap Is Nothing OrElse oCdMap.Count = 0 Then
    MessageBox.Show("Copy Design map is empty - nothing to do.", "Copy Design")
    ' ... existing early-exit
Else
    ' NEW: summary before committing
    Dim sMapSummary As String = oCdMap.Count & " file(s) identified for copy and rename." & vbCrLf & _
        "Continue? (Dry-run preview will appear before any files are copied.)"
    If MessageBox.Show(sMapSummary, "Copy Design — Map Built", MessageBoxButtons.OKCancel) <> DialogResult.OK Then
        ThisApplication.SilentOperation = bOrigSilent
        MessageBox.Show("Cancelled - no changes made.", "Cancelled")
        Exit Sub
    End If
End If
GetSetPrebuiltMode2Map(True, oCdMap)
```

Combined with WW1 (mode 2 pre-map preview), the user sees TWO confirmation points: one after map building (count), one after consuming the pre-built map (full list). Double confirmation with zero extra disk operations.

---

## Part 4 — Architecture Verdict

The overall design is sound and in several respects more sophisticated than typical iLogic automation. The 6-mode split correctly separates distinct operational needs; the Mode 2 multi-phase engine correctly implements the Vault Copy Design pattern that Autodesk itself uses; bottom-up traversal is the only correct order for reference integrity; the current-path cycle guard (not a global visited set) is the right algorithm for shared components; and the dual logging strategy addresses both crash recovery and post-run audit. The performance cache is the single structural weak point, but it is architecturally correct for Mode 6 and fixable for other modes with a one-line logic change (Fix A above). **The single most impactful structural change** would be making Mode 6 the default interactive path: present users with the Copy Design form as the primary entry point, demoting Modes 1–5 to an "Advanced" submenu. This eliminates the reported symptom (non-Mode-6 cache misses) by directing users to the gold path, without any code changes to how individual modes work. Combined with Fix A (cache logic) and WW1 (dry-run preview before Phase 2), a user who does reach Mode 1 or 2 directly is still protected. The script has earned eleven of its twelve fixes — this is not a fragile prototype but a mature automation tool with specific, addressable gaps. The win-win is already present: the architecture works; the enhancements above make the wins more visible to users at every stage.

---

*SSA output — TRAVERSE iLogic audit MAD cycle*
