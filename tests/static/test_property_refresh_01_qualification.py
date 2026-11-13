#!/usr/bin/env python3
"""Qualification gate: fail CLOSED until PROPERTY REFRESH TEST 01 is truly reusable and safe.

This is intentionally stricter than test_property_refresh_01_contract.py. It never
executes Inventor or treats a source-token check as proof of runtime safety.
Run from any directory: python tests/static/test_property_refresh_01_qualification.py
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
RULE = ROOT / "scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"
s = RULE.read_text(encoding="utf-8")
main = s.split("Sub Main()", 1)[1].split("End Sub", 1)[0] if "Sub Main()" in s else s
tests = {
    # These are explicit qualification assertions, NOT proof of safety in Inventor.
    "Core is external and independently callable": bool(re.search(r"AddVbFile|AddVbRule|ExternalRule|Imports\s+BEEXCITED", s, re.I)),
    "Traversal separated from UI wrapper": "AllReferencedDocuments" not in main and "Directory.GetFiles" not in main,
    "Eligibility separated from UI wrapper": "EligibilityReason(" not in main,
    "File mutation separated from UI wrapper": "Save2(" not in main and ".PropertySets.Item(" not in main,
    "Explicit project root input distinct from GA folder": not re.search(r"Dim root As String\s*=\s*System\.IO\.Path\.GetDirectoryName\(active\.FullFileName\)", main),
    "Vault ownership check beyond read-only attribute": bool(re.search(r"Vault.*(CheckOut|CheckedOut|Ownership|Owner)|CheckedOut.*Vault", s, re.I)) and not ("Vault ownership" in s and "not" in s),
    "Independent disk readback after save": bool(re.search(r"Documents\.Open\(|PropertySets\.Open\(", s, re.I)) and bool(re.search(r"DISK_VERIFIED|disk verification", s, re.I)),
    "Structured typed property-change record": bool(re.search(r"(Class|Structure)\s+\w*(?:PropertyChange|ChangeRecord)", s, re.I)),
    "No tab-encoded mutation records": "changes.Add(setName & vbTab" not in s,
    "Explicit recovery path for partial mutation": bool(re.search(r"Rollback|RestoreOriginal|RecoveryQuarantine", s, re.I)),
    "Distinct preview / save / disk verification counts": all(x in s for x in ("previewCount", "savedCount", "diskVerifiedCount")),
}
failed = []
for name, passed in tests.items():
    print(("PASS" if passed else "BLOCK") + ": " + name)
    if not passed:
        failed.append(name)
print(f"Qualification gate: {len(tests)-len(failed)}/{len(tests)} source assertions satisfied")
if failed:
    print("NOT QUALIFIED. This is an expected result for v0.1.0; do not enable APPLY on production files.")
    sys.exit(1)
print("Source assertions pass. Inventor compilation, Vault integration and runtime tests STILL REQUIRED.")
