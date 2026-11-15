#!/usr/bin/env python3
"""Static regression gate for PROPERTY REFRESH TEST 01.

Run: python3 scripts/ilogic/experiments/test_property_refresh_static.py
Checks source text only; cannot validate Inventor, Vault, COM, or iLogic compilation.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "scripts/ilogic/experiments/BBn_PROPERTY_REFRESH_ONLY_PWTP_01.iLogicVb"
CANDIDATE = ROOT / "scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01.iLogicVb"

def check(name, condition):
    print(("PASS" if condition else "FAIL") + " " + name)
    return bool(condition)

def main():
    if not OLD.is_file():
        print("BLOCKED: Friday baseline source missing: " + str(OLD))
        return 2
    old = OLD.read_text(encoding="utf-8-sig")
    checks = [
        check("Friday source exists", OLD.is_file()),
        check("Direct property setter retained", "p.Value = value" in old),
        check("Suffix-preserving prefix expression", '"^PJ[0-9]{5}(?=-)"' in old),
        check("Friday source contains explicit dry-run", 'Dim apply As Boolean' in old),
        check("Friday source contains Save2(False)", "doc.Save2(False)" in old),
    ]
    print("BASELINE KNOWN GAPS (not pass criteria):")
    for label, pattern in [
        ("Folder-only discovery", "SearchOption.TopDirectoryOnly"),
        ("Provenance exclusion", "SKIP-NO-TARGET-PROVENANCE"),
        ("Drawing revision reset", 'UpdateProp(custom, "REVISION"'),
        ("Opaque setter failure", 'MISSING-OR-UNWRITABLE'),
    ]:
        print(("PRESENT " if pattern in old else "ABSENT  ") + label)
    if not CANDIDATE.exists():
        print("BLOCKED: qualified candidate not present at " + str(CANDIDATE.relative_to(ROOT)))
        return 2 if all(checks) else 1
    new = CANDIDATE.read_text(encoding="utf-8-sig")
    gates = [
        check("No revision mutation in candidate", not re.search(r'UpdateProp\([^\n]*["\'](?:REVISION|Revision Number|1st REV)', new, re.I)),
        check("Default dry-run and explicit APPLY", "APPLY" in new and "DRY RUN" in new),
        check("GA reference discovery", "AllReferencedDocuments" in new),
        check("Save operation", "Save2(False)" in new),
        check("No Copy Design coupling", "Copy Design" not in new and "SaveAs(" not in new),
    ]
    # These lexical checks are necessary but insufficient: a green result is NOT
    # approval to enable APPLY or evidence of Inventor/Vault compatibility.
    print("STATIC-ONLY: drawing mapping, persisted readback, Vault guards, and runtime remain unverified")
    return 0 if all(checks + gates) else 1

if __name__ == "__main__":
    sys.exit(main())
