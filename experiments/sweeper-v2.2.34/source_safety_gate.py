"""Static fail-closed source audit; NOT an Inventor compiler or runtime validator.
Usage: python source_safety_gate.py path/to/rule.iLogicVb | --selftest
"""
import json
import re
import sys
from pathlib import Path

PATTERNS = {
    "READONLY_ATTRIBUTE_CLEAR": re.compile(r"File\.SetAttributes\s*\([^\n]*|And\s+Not\s+(?:System\.IO\.)?FileAttributes\.ReadOnly", re.I),
    "RAW_FILE_COPY_FALLBACK": re.compile(r"File\.Copy\s*\(", re.I),
    "SAVE_REQUIRES_REOPEN_PROOF": re.compile(r"\.Save2\s*\(", re.I),
}

def audit(source):
    findings = []
    for number, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("'"):
            continue
        for rule, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append({"line": number, "rule": rule, "excerpt": stripped[:180]})
    return {"status": "BLOCKED_REVIEW" if findings else "NO_PATTERN_MATCHES",
            "inventor_validated": False, "findings": findings,
            "counts": {name: sum(f["rule"] == name for f in findings) for name in PATTERNS}}

def selftest():
    sample = "' File.SetAttributes(x)\nFile.SetAttributes(p, a And Not FileAttributes.ReadOnly)\nFile.Copy(a,b)\noDoc.Save2(False)"
    result = audit(sample)
    assert result["counts"] == {"READONLY_ATTRIBUTE_CLEAR": 1, "RAW_FILE_COPY_FALLBACK": 1, "SAVE_REQUIRES_REOPEN_PROOF": 1}, result
    assert audit("' File.Copy(a,b)\n")["findings"] == []
    return True

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        selftest()
        print("SELFTEST PASS: comments ignored; hazards detected")
    elif len(sys.argv) == 2:
        print(json.dumps(audit(Path(sys.argv[1]).read_text(encoding="utf-8-sig")), indent=2))
    else:
        raise SystemExit("Usage: python source_safety_gate.py rule.iLogicVb | --selftest")
