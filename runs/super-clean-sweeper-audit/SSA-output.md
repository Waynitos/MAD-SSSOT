# SSA: Super Clean Sweeper Architecture Audit
*MAD cycle run: 2026-11-04*
*Rule: `scripts/ilogic/SUPER_CLEAN_SWEEPER.iLogicVb` v1.0.0*

---

## Verdict

**Architecture is sound. Ship v1.0.0 for testing. Fix three bugs before production use.**

The core design — SaveAs for fresh GUIDs, provenance iProperties written at save time, CS_ModelRefs enabling autonomous drawing relink — is correct and represents a genuine architectural step forward over the File.Copy approach. The DA raised six concerns; two are confirmed bugs that must be fixed, one is a critical assumption that must be verified on first test, and three are accepted risks for v1.0.

---

## Confirmed Bugs — Fix Before Production (not before tomorrow's test)

### BUG-1 (P1): WalkTree does not close documents it opens
**Severity:** Crash on large trees (100+ files)

WalkTree calls `ThisApplication.Documents.Open(sRefPath, False)` when a child is not already in the session, recurses, and returns — but never closes the document it opened. On a 200-file assembly this accumulates the entire tree in Inventor's session memory before Phase 2 begins. Combined with Phase 2 opening every file again for SaveAs, peak memory will be 2× the full tree.

**Fix for v1.1:** Track `bOpenedInWalkTree` per file. After the recursive `WalkTree(oChild, ...)` call returns, close `oChild` if we opened it in this call frame. The `oSeen` HashSet prevents re-visiting; closing is safe.

```vb
' After: WalkTree(oChild, sOldPrefix, sNewPrefix, ...)
If bOpenedInWalkHere Then
    Try : oChild.Close(True) : Catch : End Try
End If
```

### BUG-2 (P1): Phase 3 does not strip DART SHUT state tag from FileDescriptor paths

Phase 3 iterates `oDoc.File.ReferencedFileDescriptors` and looks up each `oFD3.FullFileName` in `oActualMap`. If a FileDescriptor path carries a DART SHUT tag (`<DART SHUT>` appended), the lookup will miss the entry — the old path with tag ≠ the old path without tag. The ref goes unrewritten; the new assembly loads with a broken link to the old path.

This is the same tag-stripping that WalkTree already does on `ReferencedDocumentDescriptors`. Phase 3 must do it too.

**Fix for v1.1:** Strip `<` tag from every FileDescriptor path before lookup:

```vb
Dim iAng3 As Integer = sOldRef3.IndexOf("<"c)
If iAng3 > 0 Then sOldRef3 = sOldRef3.Substring(0, iAng3).Trim()
```

---

## Critical Assumption — Verify on First Test Run (Day 1)

### ASSUMPTION-1 (P0): SaveAs(newPath, True) generates a fresh GUID

The entire provenance model — and Vault compatibility — depends on `SaveCopyAs=True` assigning a new `InternalName` GUID to the copy. If Inventor preserves the original GUID, then:
- Both old and new files carry the same GUID
- Vault treats them as the same document → catastrophic at check-in
- CS_SourceGUID becomes useless (old GUID = new file's GUID)

This was NOT verified with INVENTOR_EVENT_CAPTURE before coding (protocol step 0b was skipped for this rule). **This is the first thing to check on tomorrow's test.**

**Verification procedure:**
1. Open a test .iam in Inventor
2. Run this iLogic snippet to capture both GUIDs:
```vb
Dim oDoc = ThisApplication.ActiveDocument
Dim sOldGUID = oDoc.InternalName
MessageBox.Show("Old GUID: " & sOldGUID)
Dim sNewPath = "C:\Temp\test_copy.iam"
oDoc.SaveAs(sNewPath, True)
Dim oNew = ThisApplication.Documents.Open(sNewPath, False)
Dim sNewGUID = oNew.InternalName
oNew.Close(True)
MessageBox.Show("New GUID: " & sNewGUID & vbCrLf & "Match: " & (sOldGUID = sNewGUID))
```
3. If GUIDs differ → architecture is confirmed correct. Proceed.
4. If GUIDs match → revert to `SaveAs(newPath, False)` (rebinds doc to new path), which is confirmed to generate a new GUID, then work around the session-state implications.

---

## Accepted Risks for v1.0

### RISK-1: Silent provenance loss if new-file open fails
If `ThisApplication.Documents.Open(sNewFull2, False)` fails after a successful SaveAs, the new file has no CS_ properties. The existing log captures `NEW-OPEN-FAIL` but the skip guard will not protect the file on re-run (CS_CopyProject blank → reprocessed). **Mitigation:** Check the log for `NEW-OPEN-FAIL` entries after the run. Add a retry pass in v1.1 that opens files missing CS_CopyProject and writes provenance.

### RISK-2: Non-prefix files referenced silently not in map
Library and non-standard parts without the old prefix are not copied. Their FileDescriptors in new assemblies still point to original locations, which is correct (they don't need renaming). However, the Phase 3 lookup will silently skip them (not in oActualMap). This is correct behaviour — not a bug — but the lack of a "SKIPPED-NON-PREFIX-REF" log line makes it hard to distinguish from missed refs. Add the log line in v1.1.

### RISK-3: No atomicity / rollback
Partial runs leave the destination folder in a mixed state. The skip guard provides safe resume for already-completed files. Acceptable for v1.0 test; document as a known limitation.

---

## Summary Table

| ID | Issue | Severity | Action |
|----|-------|----------|--------|
| BUG-1 | WalkTree leaks open documents | P1 | Fix in v1.1 |
| BUG-2 | Phase 3 misses DART SHUT tagged FD paths | P1 | Fix in v1.1 |
| ASSUMPTION-1 | SaveAs GUID freshness unverified | P0 | Verify on Day 1 test |
| RISK-1 | Silent provenance loss on new-file open fail | P2 | Log entry exists; retry in v1.1 |
| RISK-2 | Non-prefix refs silently skipped | P2 | Add log line in v1.1 |
| RISK-3 | No rollback on partial run | P3 | Accepted; document |

---

## What v1.0.0 Testing Should Confirm

1. **SaveAs GUID test** — are old GUID ≠ new GUID? (see ASSUMPTION-1 procedure above)
2. **Provenance properties exist** — open a new .iam, check Inventor User Defined Properties for all 5 CS_ fields
3. **CS_ModelRefs on drawings** — open a new .idw, verify CS_ModelRefs contains pipe-delimited original model paths
4. **Phase 3 ref fix** — open the new top GA assembly directly (not via old session), verify no missing-reference dialogs for files that WERE in the rename map
5. **Skip guard** — run twice, confirm second run logs PROV-SKIP for every file

---

*SSA verdict issued 2026-11-04. Next review at v1.1 after Day 1 test results.*
