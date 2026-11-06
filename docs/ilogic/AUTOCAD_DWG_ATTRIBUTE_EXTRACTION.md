# AutoCAD DWG — Reading Block Attributes in iLogic

**Confirmed working:** AC1032 (AutoCAD 2018+), AutoCAD Mechanical 2023  
**Block:** `A1 XSTRATA` · **Tag:** `DRAWING_DESCRIPTION_2`  
**Proven:** 2026-11-06 — v2.2.29 of TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER rule

---

## Background

Native AutoCAD `.dwg` files (not Inventor DWGs) can be opened in Inventor as a
`DrawingDocument`. An earlier approach tried raw byte-scanning the binary file for
tag/value strings — this failed because AC1032 stores entity data in a compressed
bitstream, so the tag name `DRAWING_DESCRIPTION_2` does not appear as a contiguous
byte sequence. The correct approach uses Inventor's own API.

**Check whether a DWG is native AutoCAD (not Inventor):**
```vb
Dim bIsAcad As Boolean = False
Try : bIsAcad = Not ThisApplication.FileManager.IsInventorDWG(sFilePath) : Catch : End Try
```

---

## Method 1 — Sheets → AutoCADBlocks → GetPromptTextValues (Primary)

```vb
Dim sDesc As String = ""
Dim oDwgDoc As DrawingDocument = Nothing
Dim bOpened As Boolean = False
Try
    oDwgDoc = TryCast(ThisApplication.Documents.Open(sFilePath, False), DrawingDocument)
    bOpened = True
    If oDwgDoc IsNot Nothing Then
        For Each oSheet As Sheet In oDwgDoc.Sheets
            Try
                For Each oBlk As AutoCADBlock In oSheet.AutoCADBlocks
                    Dim oTags() As String = Nothing
                    Dim oVals() As String = Nothing
                    Try : oBlk.GetPromptTextValues(oTags, oVals) : Catch : Continue For : End Try
                    If oTags IsNot Nothing AndAlso oVals IsNot Nothing Then
                        For iT As Integer = 0 To oTags.Length - 1
                            Dim sTag As String = If(oTags(iT), "")
                            Dim sVal As String = If(iT < oVals.Length, If(oVals(iT), ""), "")
                            ' Exact match first; fall back to any tag containing DESCRIPTION or DRAWING
                            If String.Compare(sTag, "DRAWING_DESCRIPTION_2", True) = 0 _
                               OrElse (sDesc = "" AndAlso (sTag.ToUpper().Contains("DESCRIPTION") _
                                                           OrElse sTag.ToUpper().Contains("DRAWING"))) Then
                                sDesc = Trim(sVal)
                            End If
                        Next
                    End If
                    If sDesc <> "" Then Exit For
                Next
            Catch : End Try
            If sDesc <> "" Then Exit For
        Next
    End If
Catch ex As Exception
    ' log ex.Message
Finally
    If bOpened AndAlso oDwgDoc IsNot Nothing Then
        Try : oDwgDoc.Close(False) : Catch : End Try
    End If
End Try
```

**Notes:**
- `Open(path, False)` — `False` = do not make visible (silent open)
- Always close in `Finally` to avoid leaking document handles
- `GetPromptTextValues` returns parallel arrays: `oTags(i)` is the attribute tag name,
  `oVals(i)` is its current value

---

## Method 2 — ContainingDWGDocument COM (Fallback)

Use when Method 1 returns no blocks (some DWG layouts store inserts only in model space,
not on a named sheet). Requires AutoCAD to be installed (uses its COM object model).

```vb
If sDesc = "" Then
    Dim oDwgDoc2 As DrawingDocument = Nothing
    Dim bOpened2 As Boolean = False
    Try
        oDwgDoc2 = TryCast(ThisApplication.Documents.Open(sFilePath, False), DrawingDocument)
        bOpened2 = True
        If oDwgDoc2 IsNot Nothing Then
            Dim oAcadDb As Object = oDwgDoc2.ContainingDWGDocument
            If oAcadDb IsNot Nothing Then
                Dim oLayouts As Object = Nothing
                Try : oLayouts = oAcadDb.Layouts : Catch : End Try
                If oLayouts IsNot Nothing Then
                    For Each oLayout As Object In oLayouts
                        Dim oBlkRec As Object = Nothing
                        Try : oBlkRec = oLayout.Block : Catch : Continue For : End Try
                        If oBlkRec Is Nothing Then Continue For
                        For Each oEnt As Object In oBlkRec
                            Dim sObjName As String = ""
                            Try : sObjName = CStr(oEnt.ObjectName) : Catch : End Try
                            If sObjName = "AcDbBlockReference" Then
                                Dim oAtts As Object = Nothing
                                Try : oAtts = oEnt.GetAttributes() : Catch : End Try
                                If oAtts IsNot Nothing Then
                                    For Each oAtt As Object In oAtts
                                        Dim sTag As String = ""
                                        Dim sVal As String = ""
                                        Try : sTag = CStr(oAtt.TagString) : Catch : End Try
                                        Try : sVal = CStr(oAtt.TextString) : Catch : End Try
                                        If String.Compare(sTag, "DRAWING_DESCRIPTION_2", True) = 0 _
                                           OrElse (sDesc = "" AndAlso (sTag.ToUpper().Contains("DESCRIPTION") _
                                                                       OrElse sTag.ToUpper().Contains("DRAWING"))) Then
                                            sDesc = Trim(sVal)
                                        End If
                                    Next
                                End If
                            End If
                        Next
                        If sDesc <> "" Then Exit For
                    Next
                End If
            End If
        End If
    Catch ex As Exception
        ' log ex.Message
    Finally
        If bOpened2 AndAlso oDwgDoc2 IsNot Nothing Then
            Try : oDwgDoc2.Close(False) : Catch : End Try
        End If
    End Try
End If
```

**Notes:**
- `ContainingDWGDocument` exposes the raw AutoCAD COM database (`AcadDatabase`)
- `AcDbBlockReference` = an inserted block with attributes
- `TagString` = the attribute tag name (e.g. `DRAWING_DESCRIPTION_2`)
- `TextString` = the current attribute value

---

## Key Facts

| Item | Detail |
|---|---|
| DWG format confirmed | AC1032 (AutoCAD 2018+) |
| CAD app | AutoCAD Mechanical 2023 |
| Title block name | `A1 XSTRATA` |
| Target tag | `DRAWING_DESCRIPTION_2` |
| Fallback tag match | any tag containing `DESCRIPTION` or `DRAWING` |
| Why byte-scan fails | AC1032 entity section is compressed; tag strings are NOT plain-text in the binary |
| Rule version introduced | v2.2.29 of `TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb` |
