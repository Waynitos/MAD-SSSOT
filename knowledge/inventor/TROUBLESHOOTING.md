# Autodesk Inventor — Troubleshooting Checklists

Reusable, evidence-led fixes for Autodesk Inventor. Record the symptom, minimal checks, safe correction, validation, and source evidence. Do not assume every similar symptom has the same cause.

## INV-DWG-001 — Drawing view refuses dimensions

**Status:** VERIFIED (Inventor 2025, user retest 2026-11-11)
**Affected example:** `PJ00143-GTA-3431-6-00401.dwg`, original drawing view `28`
**Symptom:** Geometry in an existing drawing view can be selected, but placing a dimension fails or behaves incorrectly; a newly created view of the same referenced assembly allows dimensioning.

### Quick troubleshooting checklist
- [ ] Confirm that the problem affects one drawing view rather than all views.
- [ ] Confirm the drawing geometry is selectable.
- [ ] Right-click the affected drawing view and inspect **General Dimension Type**.
- [ ] If set to **True**, consider **Projected**; first check whether true 3D dimensions are intentionally required.
- [ ] On a safe editable/test copy and with appropriate Vault permissions, set **General Dimension Type → Projected**.
- [ ] Retry the **same** dimensioning operation on the **same** geometry.
- [ ] Confirm the dimension is correct and no existing drawing annotations were unintentionally affected.
- [ ] Record result and any exceptions; do not bulk-change other views without reviewing intent.

### Diagnostic evidence
Read-only `Test2` Drawing View Dimension Investigator compared original view 28 against working view 34:
| Property | Failing view 28 | Working view 34 |
|---|---|---|
| General Dimension Type | 72193 = True | 72194 = Projected |
| View Type | 10501 = Standard/Base | 10504 = Projected View |
| Drawing curves | 280 | 276 |
| Scale | 0.04 | 0.04 |
| Referenced assembly | Same | Same |
| Up to date | True | True |

**Resolution:** User changed original view's General Dimension Type from **True** to **Projected** and confirmed dimensioning works. No other changes were reported as necessary.

### Scope and precautions
This fix is verified for the reported view. It is not a universal remedy for every failed Inventor dimension. Do not confuse **View Type = Projected View** with **General Dimension Type = Projected**; the latter was the setting changed. Do not change Vault-controlled/issued drawings without proper permissions.

### References
- Detailed investigation: [iLogic drawing view investigation](../ilogic-inventor2025-drawing-view-dimension-investigation.md)
- Autodesk API: https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/GeneralDimensionTypeEnum.htm
- Autodesk troubleshooting: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Dimension-on-a-specific-drawing-view-seems-to-be-3D-instead-of-parallel-to-the-sheet-in-Inventor.html

---
**Entry policy for future software troubleshooting:** symptom → environment/version → reproducible checks → evidence → minimal fix → retest → status → source links. Keep separate software collections; promote to VERIFIED only after evidence of a successful retest.
