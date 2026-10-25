# MAD Run: Autodesk Vault Professional — On-Premise to Cloud Migration

**Status: COMPLETE ✅**
**Verdict: CONDITIONAL GO**
**Run completed: October 2026**

---

## Context

Engineering department running Autodesk Vault Professional with Inventor, AutoCAD Plant 3D, and AutoCAD — migrating from on-premise Windows Server to cloud-hosted VM (AWS/Azure). Full integration scope: Inventor (.iam/.ipt/.idw), Plant 3D (.xml/lock files/isos), AutoCAD (.dwg/.dxf/.dst), PDF, STEP/IGES, IFC, Excel BOM, DWF/DWFx.

## Files in This Run

| File | Description |
|---|---|
| `AA-brief.md` | Original advocate brief (Friday 24 Oct) |
| `DA-brief.md` | Original devil's advocate brief (Friday 24 Oct) |
| `AA-output.md` | Full AA output — strongest case FOR migration |
| `DA-output.md` | Full DA output — 13 critical failure modes identified |
| `SSA-output.md` | **Synthesiser verdict — START HERE** |

## Verdict Summary

**CONDITIONAL GO** — migration is technically viable and Autodesk-supported. Not ready to execute today. Six named conditions must be met first.

### The Six Conditions (must all be met before go-live)
1. Latency measured and within threshold (≤40ms; if 40–70ms, AVFS required)
2. Plant 3D test cases written and signed off by a Plant 3D operator
3. Version compatibility matrix confirmed for every workstation
4. Project.xml and working folder path remediation documented and tested
5. Rollback procedure executed in test environment (not just documented)
6. All checked-out files cleared before migration begins

### Highest Risk
Plant 3D — particularly the check-in direction constraint under changed working folder paths, lock file race conditions under cloud latency, and project.xml hostname references.

### Recommended Cutover Sequence
AutoCAD first → Inventor → Plant 3D last

## For Testers

See `SSA-output.md` → "What Waynito Should Bring to Testing" — 8 priority test scenarios including the Plant 3D wrong-direction test, concurrent editing race condition, large assembly timing, and iLogic rule verification.

---

*MAD cycle run under the MAD Framework Architecture. See `runs/` for other topic runs.*
