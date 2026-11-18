#!/usr/bin/env python3
"""Source-level PROPERTY REFRESH TEST 01 architecture contract.

This checks the current shared-module architecture, not Inventor execution.
Run: python tests/static/test_property_refresh_01_contract.py
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2] / "scripts/ilogic/experiments"
def read(name):
    return (ROOT / name).read_text(encoding="utf-8")

wrapper = read("BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb")
pure = read("BEEXCITED_PropertyRefreshPure.iLogicVb")
discovery = read("BEEXCITED_PropertyRefreshDiscovery.iLogicVb")
eligibility = read("BEEXCITED_PropertyRefreshEligibility.iLogicVb")
audit = read("BEEXCITED_PropertyRefreshAudit.iLogicVb")

checks = {
    "active saved document entry": "ThisApplication.ActiveDocument" in wrapper,
    "shared assembly discovery called": "BEEXCITED_PropertyRefreshDiscovery.DiscoverAssemblyModels(" in wrapper,
    "shared drawing discovery called": "BEEXCITED_PropertyRefreshDiscovery.DiscoverDrawingFolder(" in wrapper,
    "recursive assembly references in shared module": "active.AllReferencedDocuments" in discovery,
    "immediate drawing folder in shared module": "SearchOption.TopDirectoryOnly" in discovery,
    "prefix validation in shared planner": '"^PJ[0-9]{5}$"' in pure,
    "anchored prefix with suffix preservation": '"^PJ[0-9]{5}-"' in pure and "original.Substring(7)" in pure,
    "typed model and drawing plans": "Class PropertyChange" in pure and "Function PlanExistingModelProperty" in pure and "Function PlanExistingDrawingProperty" in pure,
    "named drawing arguments at call site": "filenameStem:=oldName" in wrapper and "existingDrawingNumber:=existingNumber" in wrapper,
    "drawing mapping explicitly unverified": "UNVERIFIED drawing/title-block mapping" in wrapper,
    "eligibility delegates to root classification": "BEEXCITED_PropertyRefreshRoots.ClassifyPreviewRoot(" in eligibility,
    "protected roots mandatory": "If protectedList.Count = 0 Then" in eligibility,
    "shared audit serializer": "BEEXCITED_PropertyRefreshAudit.AppendRecord(" in wrapper and "Function EncodeRecord(" in audit,
    "per-candidate audit path": "entry.FilePath = If(String.IsNullOrWhiteSpace(filePath)" in wrapper and "plan.FilePath" in wrapper,
    "dirty document guard": "If doc.Dirty Then" in wrapper and "If active.Dirty Then" in wrapper,
    "APPLY explicitly blocked": 'If apply Then' in wrapper and "APPLY BLOCKED" in wrapper,
    "no wrapper property writes": not re.search(r"\.Value\s*=", wrapper, re.I),
    "no wrapper save": not re.search(r"\bSave2\s*\(", wrapper, re.I),
    "no automatic Vault checkout": not re.search(r"\bCheckOut\s*\(", wrapper, re.I),
    "no SaveAs or component replace": not re.search(r"\b(?:SaveAs|Replace)\s*\(", wrapper, re.I),
    "no revision reset": not re.search(r"QueuePlannedChange\([^\n]*(?:REVISION|1st REV|Revision Number)", wrapper, re.I),
}
for label, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {label}")
print(f"Source contract: {sum(checks.values())}/{len(checks)}")
print("NOT A RUNTIME QUALIFICATION: Vault ownership, disk readback, recovery, drawing mapping and Inventor tests remain separate gates.")
sys.exit(0 if all(checks.values()) else 1)
