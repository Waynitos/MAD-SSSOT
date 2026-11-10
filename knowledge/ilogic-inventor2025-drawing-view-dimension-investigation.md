# iLogic ASSASSIN — Drawing view refuses dimensions: comparative evidence

**Date:** 2026-11-11
**Status:** INVESTIGATING (root-cause hypothesis; not yet verified by user)
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

## Root-cause hypothesis
The original view's True general dimension setting may explain unexpected dimension behavior. Autodesk specifically documents a similar symptom (dimension behaves in 3D rather than parallel to sheet) and recommends right-click view > General Dimension Type > Projected:
https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Dimension-on-a-specific-drawing-view-seems-to-be-3D-instead-of-parallel-to-the-sheet-in-Inventor.html

**Important caveat:** Autodesk's published symptom is dimensions appearing in 3D, while user describes inability to place dimensions. Not yet established as same root cause. Different view type and curve count remain confounders.

## Safe test (not yet performed)
On disposable copy only: note original setting, change original view 28 General Dimension Type from True to Projected, retry the exact same edge/dimension operation. Record result and any error. Do not alter released/Vault-checked-in drawing or existing dimensions without authorisation. If successful, confirm on a fresh copy; if unsuccessful, investigate geometry intents/curve properties and view differences. Avoid automatic bulk changes.

## Validation
- **TESTED:** Diagnostic rule executed by user and report captured.
- **VERIFIED:** Enum mappings against Autodesk API documentation.
- **INVESTIGATING:** Causal hypothesis; no dimension-placement retest yet.
