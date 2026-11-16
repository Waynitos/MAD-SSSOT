#!/usr/bin/env python3
"""PROPERTY REFRESH TEST 01 source audit (not an Inventor qualification gate).

Exit 0 means this *audit ran*, not that APPLY is safe. Exit 2 means a
required source is missing; exit 1 means a source invariant regressed.
No Inventor, Vault, COM, VB compiler or runtime is exercised.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
DIR = ROOT / "scripts/ilogic/experiments"
BASELINE = DIR / "BBn_PROPERTY_REFRESH_ONLY_PWTP_01.iLogicVb"
PURE = DIR / "BEEXCITED_PropertyRefreshPure.iLogicVb"
PREVIEW = DIR / "BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"
DIRECT = DIR / "BEEXCITED_PROPERTY_REFRESH_DIRECT_TEST_01.iLogicVb"

def main():
    sources = {}
    for name, path in [("Friday baseline", BASELINE), ("shared pure planner", PURE),
                       ("versioned preview", PREVIEW), ("direct test", DIRECT)]:
        if not path.is_file():
            print("BLOCKED missing " + name + ": " + str(path))
            return 2
        sources[name] = path.read_text(encoding="utf-8-sig")
    old, pure, preview, direct = (sources[n] for n in
        ("Friday baseline", "shared pure planner", "versioned preview", "direct test"))
    tests = {
        "baseline direct property setter": "p.Value = value" in old,
        "baseline prefix regex": '"^PJ[0-9]{5}(?=-)"' in old,
        "shared planner validates PJ#####": '"^PJ[0-9]{5}$"' in pure,
        "shared planner preserves suffix": "original.Substring(7)" in pure,
        "preview delegates model planning to shared module":
            "BEEXCITED_PropertyRefreshPure.PlanExistingModelProperty(" in preview,
        "preview delegates drawing planning to shared module":
            "BEEXCITED_PropertyRefreshPure.PlanExistingDrawingProperty(" in preview,
        "preview discovers GA references": "asm.AllReferencedDocuments" in preview,
        "preview discovers drawing folder": "SearchOption.TopDirectoryOnly" in preview,
        "preview explicitly blocks APPLY":
            bool(re.search(r"If apply Then\s*MessageBox.Show\(\"APPLY BLOCKED", preview)),
        "preview contains no write/save execution":
            "doc.Save2(" not in preview and not bool(re.search(r"\.Item\([^\n]+\)\.Value\s*=", preview)),
        "preview has no revision assignment":
            not bool(re.search(r"\.Item\(\"(?:REVISION|Revision Number|1st REV)\"\)\.Value\s*=", preview, re.I)),
        "direct test still has duplicated planner":
            "Function ChangePrefix(" in direct and "Sub AddModelPlan(" in direct,
        "direct test has unqualified APPLY path":
            "If apply Then" in direct and "doc.Save2(False)" in direct,
    }
    for name, passed in tests.items():
        print(("PASS " if passed else "FAIL ") + name)
    print("KNOWN BLOCKERS: no single shared mutation/readback engine; direct-test duplication;")
    print("no Vault checkout verification; no persisted reopen/readback; drawing title-block")
    print("mapping unverified; no Inventor/Vault runtime or compilation evidence.")
    print("AUDIT ONLY: lexical assertions cannot establish functional safety.")
    return 0 if all(tests.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
