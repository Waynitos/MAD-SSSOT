#!/usr/bin/env python3
"""PROPERTY REFRESH TEST 01: offline source-contract checks, not Inventor tests.

Run from repository root: python3 scripts/ilogic/experiments/tests/test_property_refresh_source_contract.py
Does not import or reimplement VB algorithms, access Inventor, or modify project files.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "scripts/ilogic/experiments"
FILES = {
    "pure": "BEEXCITED_PropertyRefreshPure.iLogicVb",
    "eligibility": "BEEXCITED_PropertyRefreshEligibility.iLogicVb",
    "readback": "BEEXCITED_PropertyRefreshReadback.iLogicVb",
}
def check(name, condition):
    print(("PASS" if condition else "FAIL") + " " + name)
    return bool(condition)

def main():
    src = {}
    for key, filename in FILES.items():
        path = BASE / filename
        if not path.is_file():
            print("FAIL missing " + str(path))
            return 1
        src[key] = path.read_text(encoding="utf-8-sig")
    pure, eligibility, readback = (src[k] for k in ("pure", "eligibility", "readback"))
    checks = [
        ("pure has exactly five public functions", len(re.findall(r"^\s*Public Function\b", pure, re.M)) == 5),
        ("pure does not call Inventor API", re.search(r"\bInventor\.", pure, re.I) is None),
        ("pure has no UI prompts", re.search(r"\b(InputBox|MessageBox|MsgBox)\s*\(", pure, re.I) is None),
        ("project prefix strictly validated", '"^PJ[0-9]{5}$"' in pure),
        ("existing prefix anchored", '"^PJ[0-9]{5}-"' in pure),
        ("prefix suffix retained", "original.Substring(7)" in pure),
        ("drawing planner requires filename identity", "fileBaseName.Substring(0, 7)" in pure),
        ("drawing mapping remains hardcoded (qualification blocker)", '.PropertyName = "DRAWING_NUMBER"' in pure),
        ("eligibility rejects absent protected roots", "protectedList.Count = 0" in eligibility),
        ("eligibility blocks read-only", "FileAttributes.ReadOnly" in eligibility),
        ("eligibility explicitly preview-only", "PreviewCandidateRequiresVaultOwnershipAndDirtyChecks" in eligibility),
        ("readback is open-document only", "doc.PropertySets.Item(setName).Item(propertyName).Value" in readback),
        ("readback does not save", re.search(r"\b(?:doc\.)?Save(?:As|2)?\s*\(", readback, re.I) is None),
        ("readback acknowledges persistence blocker", "persisted verification must reopen" in readback),
    ]
    passed = sum(check(name, result) for name, result in checks)
    print(f"{passed}/{len(checks)} source-contract checks passed")
    print("LIMITATION: structural assertions only; no VB compilation, Inventor execution, Vault, APPLY, or disk persistence validation.")
    return 0 if passed == len(checks) else 1

if __name__ == "__main__":
    sys.exit(main())
