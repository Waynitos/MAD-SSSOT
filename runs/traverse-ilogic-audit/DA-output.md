# DA Output — TRAVERSE iLogic Audit

**Role:** Devil's Advocate (strongest case against current implementation)
**MAD Run:** traverse-ilogic-audit
**File audited:** TRAVERSE_fixed.iLogicVb (8052 lines)

---

## The case against: twelve structural weaknesses

### 1. Performance cache invalidation — the direct cause of the user's reported symptom

`oProcessedResults` (Dictionary(Of String, Boolean)) caches whether a document's subtree contained any changes, keyed by full filename. It is cleared between Mode 4 batch passes, but NOT between sequential Mode 1/2 re-runs within the same Inventor session, and NOT within a single Mode 1 traversal when the same document is reached from a second parent branch.

The failure: Document X is reached from Branch A, explored, found to need no changes, and cached as False. Branch B then reaches Document X again. Because the cache returns False immediately, the traversal does not re-enter Document X to check whether changes made while processing Branch A (renaming a sibling of X, for example) have now made X's internal references stale.

This is exactly the user's described symptom — "cached versions of historic subs missed the renaming of define pass runs." A sub-assembly explored early in the traversal is cached as unchanged; a later pass at the same document (from a different branch, or in a re-run) short-circuits on the cached result and never updates the file that now needs updating.

The cache is architecturally correct only for Mode 6, where a complete rename map is pre-built before any disk writes, so the traversal's only job is to apply a known-complete map. For Mode 1 (incremental, bottom-up, discovering renames as it goes), caching "no changes" is wrong because the tree state changes during the traversal itself.

### 2. Phase 3 depth ordering — path length is not depth

Phase 3 sorts new target files before fixing internal references:

```vb
oNewTargets.Sort(Function(a, b2) b2.Length.CompareTo(a.Length))
```

Path STRING LENGTH is used as a proxy for assembly CONTAINMENT DEPTH. These are not the same thing.

A file at depth 2 in a long directory path (`C:\ProjectData\Engineering\Structures\2026\PJ00193-3620-MainAsm\SubFolder\Bracket.ipt` — 87 chars) will sort BEFORE a file at depth 5 in a short directory path (`C:\Work\A\B\C\D\Pin.ipt` — 24 chars).

Result: a parent assembly is opened and saved in Phase 3 BEFORE its children have had their own internal references fixed. The parent's save captures stale child-reference state — the children still point at OLD file paths at the moment the parent is saved. This reproduces exactly the "re-run needed to catch misses" behaviour the user described, and it occurs even in Mode 6 where the cache issue (weakness 1) does not apply.

The correct sort key is Inventor document containment depth (counted by assembly nesting level), not path character count.

### 3. GoTo control flow — skipped initialisations and unrestored state

Three GoTo labels span large blocks of code:

- `GoTo SkipBatchMode` (inside Mode 6 block, ~line 454) — jumps past all of Mode 4 and the main Mode 1 single-prefix traversal
- `GoTo AfterSingleTraversal` (~lines 543, 578) — jumps past the `ProcessLevel` call
- `GoTo Mode2Phase2` (~line 783) — jumps from inside the pre-built map branch INTO the middle of the Phase 2 copy block

The `GoTo Mode2Phase2` jump is the most dangerous. The normal path initialises `iMapBuilt = 0` and `iMapSkipped = 0` before the map-building loop. The GoTo path sets `iMapBuilt` inside the pre-built map loop (correct) but jumps past `iMapSkipped`'s initialisation. If `iMapSkipped` is used in the summary log after `Mode2Phase2:`, it reads an uninitialised value.

More critically: `ThisApplication.SilentOperation = True` is set at ~line 351, BEFORE the Mode 6 form is shown. If the user cancels the Copy Design config form (line ~389: `MessageBox.Show("Cancelled...")`), the function restores `SilentOperation` correctly — but if an exception fires between SilentOperation being set and the mode-selection block, the `Finally`-less error path may leave SilentOperation permanently True for the Inventor session, suppressing all subsequent dialogs until Inventor is restarted.

### 4. Failed Phase 2 copy → Phase 4 repoints to non-existent file

Phase 2 clears the ReadOnly attribute on source files before copying:

```vb
Try
    Dim oA As System.IO.FileAttributes = System.IO.File.GetAttributes(sOldFull)
    If (oA And System.IO.FileAttributes.ReadOnly) = ... Then
        System.IO.File.SetAttributes(sOldFull, oA And Not ...)
    End If
Catch : End Try
```

If this attribute-clear fails (bare Catch, logged nowhere) and the subsequent File.Copy also fails, `iCopyFailed` is incremented and execution continues. The target file (`sNewFull`) does not exist on disk.

Phase 3 then skips the missing target (`If Not System.IO.File.Exists(sNewFull) Then Continue For`). Phase 4 still attempts to repoint live session occurrences to `sNewFull` — a file that was never created. Inventor accepts the repoint in memory (the occurrence's internal path is updated), and the assembly is saved pointing at a non-existent file. On the next open, Inventor reports a broken reference with no indication that this was caused by a failed copy in a previous run.

There is no post-Phase-2 guard that aborts Phases 3 and 4 if any copy failed.

### 5. Module-level state leak — stale pre-built map survives a cancelled run

`GetSetPrebuiltMode2Map(True, map)` stores the Mode 6 master map in module-level state. It is cleared after consuming it (`GetSetPrebuiltMode2Map(True, Nothing)` at ~line 782) — but only if Phase 1 completes and the GoTo jumps to Phase 2.

If the user:
1. Starts Mode 6
2. Cancels the Copy Design config form (line ~389) OR cancels the batch selection form (line ~403)

...the cancel path calls `MessageBox.Show("Cancelled")` and `Exit Sub` WITHOUT clearing the pre-built map. If Mode 6 had already built a partial map before the cancel (it hasn't in the normal path, since BuildCopyDesignRenameMap runs before ShowBatchSelectionForm — but the order depends on implementation), that map persists in module state.

More concretely: the `GoTo SkipBatchMode` jump at ~line 454 means Mode 6 falls through to Mode 2 code. If a previous run left a stale map in module state and Mode 2 is run directly (not via Mode 6), the stale pre-built map is consumed by `GetSetPrebuiltMode2Map()` at ~line 770 and used as if it were intentionally built for this run — silently performing the wrong renames.

### 6. AllReferencedDocuments misses suppressed, unloaded, and non-document references

`oAsmDoc.AllReferencedDocuments` only returns documents currently LOADED in the Inventor session. Several reference types are missed:

- **Suppressed occurrences**: an occurrence suppressed in the active Level of Detail representation has its document NOT loaded — it exists on disk and in the assembly's FileDescriptors, but not in AllReferencedDocuments
- **Positional representations**: components hidden in a positional rep may not be loaded
- **External model states**: a part referenced as an external model state may not be in AllReferencedDocuments if not currently active
- **.xlsx parameter tables**: linked parameter spreadsheets appear in ReferencedFileDescriptors (the script handles these) but if the xlsx is referenced by a SUPPRESSED assembly, that assembly isn't in AllReferencedDocuments, so its FileDescriptors aren't scanned either — the xlsx is missed entirely

The supplemental `File.ReferencedFileDescriptors` scan mitigates some of this, but only for LOADED documents — it cannot reach a suppressed assembly's file descriptors if that assembly document was never opened.

### 7. Snapshot file — stale after manual intervention, no integrity check

The original-state snapshot (`_Original_Featured_Files_Folder_Location.txt`) is written on first run and never overwritten. This is correct for protecting the true starting state against subsequent runs.

However:
- The snapshot records file paths at snapshot time. If the user manually moves or renames files between the first and second runs (outside Inventor, via Windows Explorer or Vault), the snapshot records paths that no longer exist
- The snapshot has no integrity check — it never verifies recorded paths exist on disk
- A revert operation using the stale snapshot would attempt to repoint occurrences at non-existent old paths, creating broken references
- There is no timestamp or run-count in the snapshot indicating HOW MANY runs have modified the tree since the snapshot was taken — a user looking at a snapshot from 3 months ago has no way to know it represents the state before the first of six runs

### 8. Desktop log path — silent failure in corporate/redirected environments

```vb
Dim sLogFilePath As String = System.Environment.GetFolderPath(
    System.Environment.SpecialFolder.Desktop) & "\Traverse_Rename_Log_..."
Try
    System.IO.File.WriteAllText(sLogFilePath, ...)
Catch
    ' carry on anyway
End Try
```

On a corporate machine with Group Policy folder redirection, `SpecialFolder.Desktop` resolves to a UNC path (`\\fileserver\users\wayne\Desktop`). If the fileserver is slow, offline, or the path is inaccessible from the Inventor process context, the initial WriteAllText fails silently. ALL subsequent AppendAllText calls also fail silently. The entire crash log is lost — every bare `Catch : End Try` around AppendAllText throughout the file produces no output.

The run proceeds with no crash log. If Inventor crashes mid-run, there is no disk record of what it was doing — the entire benefit of fix 7 (disk-flushed crash log) is negated.

### 9. No mid-run cancellation path

Once the traversal starts (after the confirmation dialogs), there is no way for the user to cancel. The rule runs to completion or crashes.

On a large assembly (hundreds of files, each requiring SaveAs and Documents.Open), a single run can take 20–40 minutes. If the user realises they entered the wrong Find or Replace text 2 minutes in, they must either:
1. Wait for the full run to complete with wrong renames (then manually undo)
2. Force-kill Inventor — leaving the assembly tree in an indeterminate state (some files renamed, some not, some assemblies saved with mixed old/new references)

There is no partial-run detection or recovery path — the Mode 5 verify pass can detect misses, but cannot distinguish "correctly not renamed" from "should have been renamed but wasn't."

### 10. Excel COM state inherited across runs

```vb
Try
    oExcelApp = GetObject(, "Excel.Application")
    bExcelAlertsOriginal = oExcelApp.DisplayAlerts
    oExcelApp.DisplayAlerts = False
Catch
    Try
        oExcelApp = CreateObject("Excel.Application")
        ...
    Catch
        oExcelApp = Nothing
    End Try
End Try
GetSetExcelApp(True, oExcelApp)
```

If the previous run crashed while Excel was open with DisplayAlerts = False, the NEXT run's `GetObject` retrieves that existing Excel instance — with DisplayAlerts still False from the previous run. `bExcelAlertsOriginal` captures False (the current bad state), so the finally-restore sets DisplayAlerts back to False instead of True. Excel silently suppresses all its own dialogs for the rest of the session.

Also: if `oExcelApp = Nothing` (both GetObject and CreateObject failed), `GetSetExcelApp(True, Nothing)` stores Nothing. Any later call to `GetSetExcelApp()` that retrieves this Nothing and calls methods on it produces a NullReferenceException — likely swallowed by a surrounding Catch, meaning Excel-dependent operations (xlsx param table fixes) silently do nothing.

### 11. Mode 3 session warning is advisory only — leaves tree inconsistent

The Mode 3 warning ("N files from the original folder are open in this session") is advisory — the user clicks OK and the consolidation proceeds. Files currently open in Inventor cannot be SaveAs'd to a new location; the attempt produces E_FAIL.

The script's response is to skip the locked file ("locked files will be skipped and noted in the log"). But "noted in the log" means noted in the Desktop crash log — which, as established in weakness 8, may itself be failing silently.

After Mode 3 completes with skipped files:
- The occurrence in the assembly STILL points at the OLD (unconsolidated) path
- No summary of skipped files is shown to the user after the run (unlike the Mode 5 verify which shows a count)
- The user must manually cross-reference the crash log (if it wrote successfully) to discover which files need re-running
- Re-running Mode 3 after a fresh Inventor session will pick up the missed files — but only if the user knows to do this

### 12. sFind = sReplace placeholder in Mode 6 — latent Phase 4 matching risk

At ~line 437, Mode 6 sets `sFind = sReplace` as a placeholder before falling through to Mode 2:

```vb
sFind = sReplace  ' placeholder; Phase 1 uses pre-built map
```

Phase 1 is bypassed (GoTo Mode2Phase2), so this placeholder never matters for map building. However, if any Phase 4 code (live occurrence repointing) uses `sFind` for matching — e.g., `If occ.Name.Contains(sFind)` to decide which occurrences to repoint — it would match against `sReplace` (the NEW project number), finding newly-renamed occurrences and potentially attempting to re-rename or re-repoint them.

Whether this is a live bug depends on Phase 4's implementation (not fully read in this audit), but the placeholder assignment is a trap that makes the code's intent ambiguous and creates a correctness dependency between two widely-separated code sections with no comment linking them.

---

*DA output — TRAVERSE iLogic audit MAD cycle*
