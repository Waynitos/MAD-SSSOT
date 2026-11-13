#!/usr/bin/env python3
"""Offline source contract gate for PROPERTY REFRESH TEST 01. No Inventor execution."""
from pathlib import Path
import re
import sys

RULE = Path(__file__).resolve().parents[2] / "scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"
source = RULE.read_text(encoding="utf-8")
checks = {
    "active document": "ThisApplication.ActiveDocument" in source,
    "GA assembly recursive references": "asm.AllReferencedDocuments" in source,
    "GA drawing folder top level": "SearchOption.TopDirectoryOnly" in source,
    "project prefix validation": '"^PJ[0-9]{5}$"' in source,
    "explicit APPLY": 'String.Equals(mode.Trim(), "APPLY", StringComparison.Ordinal)' in source,
    "dirty active document guard": "If active.Dirty Then" in source,
    "dirty referenced document guard": "If doc.Dirty Then" in source,
    "readonly guard": "FileAttributes.ReadOnly" in source,
    "project path containment": "OUTSIDE-GA-FOLDER-TREE" in source,
    "dry-run before write": "If apply Then" in source,
    "part number update": '"Part Number"' in source,
    "specification update": '"SPECIFICATION"' in source,
    "drawing number update": '"DRAWING_NUMBER"' in source,
    "post-save in-memory readback": "Post-save in-memory property readback failed" in source,
    "per-file log": "WriteLine(log," in source,
    "no automatic Vault checkout": not re.search(r"\\bCheckOut\\s*\\(", source, re.I),
    "no SaveAs": not re.search(r"\\bSaveAs\\s*\\(", source, re.I),
    "no component replace": not re.search(r"\\bReplace\\s*\\(", source, re.I),
    "no revision reset": not re.search(r'QueueChange\\([^\\n]*"(?:REVISION|1st REV|Revision Number)"', source, re.I),
}
for label, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
# Pure-Python behavior mirrors the *documented* regex contract; does not execute VB.
def replace_prefix(value, pj):
    return re.sub(r"^PJ[0-9]{5}(?=-)", pj, value, flags=re.I)
cases = [
    ("PJ00201-3410-01", "PJ00999-3410-01"),
    ("pj00201-A", "PJ00999-A"),
    ("PJ00201", "PJ00201"),
    ("ABC-PJ00201-A", "ABC-PJ00201-A"),
    ("PJ00201_X", "PJ00201_X"),
    ("PJ00999-A", "PJ00999-A"),
]
for before, expected in cases:
    actual = replace_prefix(before, "PJ00999")
    ok = actual == expected
    checks[f"prefix case {before}"] = ok
    print(f"{'PASS' if ok else 'FAIL'}: prefix {before} -> {actual}")
print(f"RESULT: {sum(checks.values())}/{len(checks)} passed")
if not all(checks.values()):
    sys.exit(1)
