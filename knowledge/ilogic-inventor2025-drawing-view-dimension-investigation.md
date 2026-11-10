# iLogic ASSASSIN — Drawing view refuses dimensions: comparative evidence

**Date:** 2026-11-11
**Status:** VERIFIED — user confirmed dimensioning works after changing the original view to Projected on 2026-11-11
**Drawing:** PJ00143-GTA-3431-6-00401.dwg
**Diagnostic:** read-only Test2 Drawing View Dimension Investigator (user executed in Inventor 2025)

## Evidence
Original view 28: ViewType=10501 (standard/base), GeneralDimensionType=72193 (True), Scale=0.04, DrawingCurves.Count=280, UpToDate=True, Suppressed=False.
Working view 34: ViewType=10504 (projected), GeneralDimensionType=72194 (Projected), Scale=0.04, DrawingCurves.Count=276, UpToDate=True, Suppressed=False.
Both reference the same assembly PJ00143-343-V0-20-10.iam; widths/heights and orientation are almost identical. Camera eye distances differ but target and up vector nearly match.

## Official API interpretation
Autodesk DrawingViewTypeEnum: 10501=kStandardDrawingViewType; 10504=kProjectedDrawingViewType.
https://help.autodesk.com/cloudhelp/2024/ENU/Inventor-API/files/DrawingViewTypeEnum.htm
Autodesk GeneralDimensionTypeEnum: 72193=kTrueGeneralDimension; 72194=kProjectedGeneralDimension.
https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/GeneralDimensionTypeEnum.htm

## Confirmed cause and resolution
User confirmed that changing the original view's General Dimension Type from True to Projected restored dimensioning. This is a verified fix for the reported case. Autodesk specifically documents a similar symptom (dimension behaves in 3D rather than parallel to sheet) and recommends right-click view > General Dimension Type > Projected:
https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Dimension-on-a-specific-drawing-view-seems-to-be-3D-instead-of-parallel-to-the-sheet-in-Inventor.html

**Scope:** The fix is confirmed for this drawing/view, not a universal diagnosis for all Inventor dimensioning failures. View type and curve-count differences were observed but did not need modification.

## Verified test
The user manually changed the affected view to Projected and confirmed: "Yes projected changed it - & we are ok now." No automated mutation or additional changes to the view were reported.

## Validation
- **TESTED:** Diagnostic rule executed by user and report captured.
- **VERIFIED:** Enum mappings against Autodesk API documentation.
- **VERIFIED:** User reports dimensioning restored by changing General Dimension Type from True to Projected.
- **NOT TESTED:** Automated repair or application to other drawings; no claim of Inventor runtime access by assistant.
