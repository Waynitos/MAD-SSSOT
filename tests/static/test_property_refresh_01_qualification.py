#!/usr/bin/env python3
"""Fail-closed source qualification for the SHARED Property Refresh 01 architecture.

This is a structural gate, not VB compilation, a semantic test, or Inventor/Vault
runtime evidence. A green source gate must NEVER authorize APPLY on its own.
Run: python tests/static/test_property_refresh_01_qualification.py
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2] / "scripts/ilogic/experiments"

def source(name):
    return (ROOT / ("BEEXCITED_" + name + ".iLogicVb")).read_text(encoding="utf-8")

wrapper = source("PROPERTY_REFRESH_TEST_01_v0_1_0")
pure = source("PropertyRefreshPure")
discovery = source("PropertyRefreshDiscovery")
eligibility = source("PropertyRefreshEligibility")
roots = source("PropertyRefreshRoots")
audit = source("PropertyRefreshAudit")
readback = source("PropertyRefreshReadback")
all_source = "\n".join((wrapper, pure, discovery, eligibility, roots, audit, readback))

def has(pattern, text):
    return re.search(pattern, text, re.I | re.S) is not None

checks = {
    "Shared discovery invoked by standalone wrapper":
        "BEEXCITED_PropertyRefreshDiscovery.DiscoverAssemblyModels(" in wrapper
        and "BEEXCITED_PropertyRefreshDiscovery.DiscoverDrawingFolder(" in wrapper,
    "Shared pure property planner invoked by wrapper":
        "BEEXCITED_PropertyRefreshPure." in wrapper
        and "Class PropertyChange" in pure,
    "Shared protected-root classification invoked":
        "BEEXCITED_PropertyRefreshRoots.ClassifyPreviewRoot(" in eligibility
        and "If protectedList.Count = 0 Then" in eligibility,
    "Shared per-file audit invoked":
        "BEEXCITED_PropertyRefreshAudit.AppendRecord(" in wrapper
        and "entry.FilePath = If(String.IsNullOrWhiteSpace(filePath)" in wrapper,
    "Wrapper keeps APPLY fail-closed":
        "APPLY BLOCKED" in wrapper and "If apply Then" in wrapper
        and not has(r"\bSave2\s*\(|\bSaveAs\s*\(|\bCheckOut\s*\(", wrapper)
        and not has(r"\.Value\s*=", wrapper),
    "No arbitrary drawing revision reset":
        not has(r"QueuePlannedChange\([^\n]*(?:REVISION|1st REV|Revision Number)", wrapper),
    "Shared core is independent of Copy Design":
        not has(r"CopyDesign|ComponentOccurrence\.Replace\(", pure + discovery + eligibility + roots + audit + readback),
    # The remaining gates are intentionally strict and currently expected to BLOCK.
    # Do not satisfy these with comments, stubs, or token-only claims.
    "Authoritative Vault checkout ownership implementation":
        has(r"Function\s+VerifyVaultOwnership\s*\(", all_source)
        and has(r"VerifyVaultOwnership\s*\(", wrapper)
        and not has(r"Function\s+VerifyVaultOwnership[^\n]*\n\s*Return\s+True", all_source),
    "Independent persisted disk readback implementation":
        has(r"Function\s+VerifyPersisted(?:File|Property)\s*\(", all_source)
        and has(r"VerifyPersisted(?:File|Property)\s*\(", wrapper)
        and not has(r"does not verify persisted disk state", readback),
    "Approved drawing property mapping implemented":
        has(r"Function\s+VerifyDrawingPropertyMapping\s*\(", all_source)
        and has(r"VerifyDrawingPropertyMapping\s*\(", wrapper)
        and not has(r"UNVERIFIED drawing/title-block mapping", wrapper),
    "Per-file recovery implementation":
        has(r"Function\s+(?:RollbackPropertyChanges|RecoverPartialWrite)\s*\(", all_source)
        and has(r"(?:RollbackPropertyChanges|RecoverPartialWrite)\s*\(", wrapper),
    "Distinct preview, saved and disk-verified outcomes":
        all(has(r"\b" + name + r"\b", all_source)
            for name in ("previewCount", "savedCount", "diskVerifiedCount")),
    "Bounded external Inventor COM watchdog with recovery":
        has(r"Function\s+RunWithExternalWatchdog\s*\(", all_source)
        and has(r"RunWithExternalWatchdog\s*\(", wrapper),
}
for name, passed in checks.items():
    print(("PASS" if passed else "BLOCK") + ": " + name)
count = sum(checks.values())
print(f"Source qualification: {count}/{len(checks)} assertions satisfied")
print("Source assertions do not establish VB compilation, Inventor/Vault compatibility, "
      "disk persistence, or safe APPLY. Host validation and human authorization required.")
if count != len(checks):
    print("NOT QUALIFIED: keep APPLY blocked; do not modify source/production files.")
sys.exit(0 if count == len(checks) else 1)
