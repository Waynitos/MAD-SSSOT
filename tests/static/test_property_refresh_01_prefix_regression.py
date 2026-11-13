#!/usr/bin/env python3
"""Offline behavioral regression for BEEXCITED Property Refresh 01 prefix mapping.

This test is a reference model, NOT Inventor execution and NOT a claim that the
VB implementation compiled. It also asserts the actual candidate's regex and
guards against broad string replacement.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"
text = SOURCE.read_text(encoding="utf-8")
prefix_pattern = r"^PJ[0-9]{5}(?=-)"
target = "PJ00333"

cases = [
    ("PJ00201-3410-01", "PJ00333-3410-01"),
    ("pj00201-3410-01", "PJ00333-3410-01"),
    ("PJ00201", "PJ00201"),
    ("PJ00201X-3410", "PJ00201X-3410"),
    ("ABC-PJ00201-3410", "ABC-PJ00201-3410"),
    ("PJ00201-3410-PJ00201", "PJ00333-3410-PJ00201"),
    ("PJ00333-3410", "PJ00333-3410"),
    ("PJ00201--", "PJ00333--"),
    ("PJ00201-001", "PJ00333-001"),
    ("PJ002010-3410", "PJ002010-3410"),
    ("PJ00201_3410", "PJ00201_3410"),
    ("PJ00201/3410", "PJ00201/3410"),
    ("PJ00201 -3410", "PJ00201 -3410"),
    ("pj00201-3410-pj00201", "PJ00333-3410-pj00201"),
    ("PJ00201-3410\tNOTE", "PJ00333-3410\tNOTE"),
    ("", ""),
]

errors = []
for old, expected in cases:
    actual = re.sub(prefix_pattern, target, old, flags=re.I)
    if actual != expected:
        errors.append(f"mapping {old!r}: expected {expected!r}, got {actual!r}")
    again = re.sub(prefix_pattern, target, actual, flags=re.I)
    if again != actual:
        errors.append(f"not idempotent for {old!r}")

required = [
    'Regex.Replace(oldValue, "^PJ[0-9]{5}(?=-)", pj, System.Text.RegularExpressions.RegexOptions.IgnoreCase)',
    'Regex.IsMatch(pj, "^PJ[0-9]{5}$")',
]
for token in required:
    if token not in text:
        errors.append(f"VB source contract changed: {token}")
if re.search(r"Replace\(oldValue,\s*oldProject", text, re.I):
    errors.append("potential broad string replacement found")
if "QueuePrefix(doc, custom, \"SPECIFICATION\"" not in text:
    errors.append("SPECIFICATION mapping missing")
if "QueuePrefix(doc, design, \"Part Number\"" not in text:
    errors.append("Part Number mapping missing")
if 'QueueChange(doc, "Inventor User Defined Properties", "DRAWING_NUMBER"' not in text:
    errors.append("DRAWING_NUMBER mapping missing")
if "doc.Save2(False)" not in text:
    errors.append("save operation missing")
if "doc.Dirty" not in text:
    errors.append("dirty-document guard missing")

print(f"Prefix fixtures: {len(cases)}; checks: {len(cases)*2+len(required)+7}; failures: {len(errors)}")
for error in errors:
    print("FAIL:", error)
if errors:
    sys.exit(1)
print("PASS: offline prefix fixtures and source assertions only; not a safety qualification.")
