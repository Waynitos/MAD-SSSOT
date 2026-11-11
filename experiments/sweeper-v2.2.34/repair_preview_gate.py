"""Offline, fail-closed preview gate for Existing Target Repair.
No Inventor automation, renames, writes to CAD files, or Vault operations.
Input is a JSON inventory produced by a separately verified discovery stage.
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

EXTENSIONS = {".iam", ".ipt", ".idw", ".dwg", ".ipn"}

def under_root(path, root):
    p = os.path.normcase(os.path.abspath(path))
    r = os.path.normcase(os.path.abspath(root))
    return os.path.commonpath([p, r]) == r

def preview(inventory):
    root = os.path.abspath(inventory["target_root"])
    substitutions = inventory["substitutions"]
    if not isinstance(substitutions, list) or len(substitutions) > 5:
        raise ValueError("Expected at most five substitutions")
    if any(not isinstance(x, list) or len(x) != 2 or not all(isinstance(y, str) for y in x) or not x[0] for x in substitutions):
        raise ValueError("Each substitution must be [nonempty search, replacement]")
    blockers = []
    planned = []
    entries = inventory["files"]
    if not entries:
        blockers.append("EMPTY_INVENTORY")
    if not inventory.get("discovery_complete", False):
        blockers.append("DISCOVERY_NOT_CERTIFIED")
    if not inventory.get("reverse_references_complete", False):
        blockers.append("REVERSE_REFERENCES_NOT_CERTIFIED")
    if not inventory.get("frame_generator_verified", False):
        blockers.append("FRAME_GENERATOR_NOT_VERIFIED")
    if not inventory.get("vault_clearance_verified", False):
        blockers.append("VAULT_CLEARANCE_NOT_VERIFIED")
    if not inventory.get("profiling_available", False):
        blockers.append("PROFILING_NOT_AVAILABLE")
    destinations = defaultdict(list)
    seen = set()
    for item in entries:
        src = os.path.abspath(item["path"])
        ext = Path(src).suffix.lower()
        if not under_root(src, root):
            blockers.append("OUTSIDE_ROOT:" + src)
        if ext not in EXTENSIONS:
            blockers.append("UNSUPPORTED_EXTENSION:" + src)
        key = os.path.normcase(src).casefold()
        if key in seen:
            blockers.append("DUPLICATE_SOURCE:" + src)
        seen.add(key)
        if not os.path.isfile(src):
            blockers.append("MISSING_SOURCE:" + src)
        if not item.get("references_resolved", False):
            blockers.append("UNRESOLVED_REFERENCES:" + src)
        if not item.get("ownership_verified", False):
            blockers.append("OWNERSHIP_UNKNOWN:" + src)
        if not item.get("writable_verified", False):
            blockers.append("WRITABILITY_UNKNOWN:" + src)
        stem = Path(src).stem
        newstem = stem
        for search, replacement in substitutions:
            import re
            newstem = re.sub(re.escape(search), lambda _: replacement, newstem, flags=re.IGNORECASE)
        if not newstem or newstem.endswith((".", " ")) or any(c in newstem for c in '<>:"/\\|?*'):
            blockers.append("INVALID_TARGET_NAME:" + src)
        dst = os.path.join(os.path.dirname(src), newstem + Path(src).suffix)
        destinations[os.path.normcase(dst).casefold()].append(src)
        if os.path.normcase(src).casefold() != os.path.normcase(dst).casefold() and os.path.exists(dst):
            blockers.append("DESTINATION_EXISTS:" + dst)
        planned.append({"source": src, "destination": dst, "changed": src != dst})
    for sources in destinations.values():
        if len(sources) > 1:
            blockers.append("DESTINATION_COLLISION:" + " | ".join(sources))
    # Even with no blockers this is preview-only. No mutation entry point exists.
    return {"approved_for_mutation": False, "preview_only": True,
            "preflight_blockers": sorted(set(blockers)), "plan": planned}

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python repair_preview_gate.py inventory.json")
    with open(sys.argv[1], encoding="utf-8") as handle:
        inventory = json.load(handle)
    print(json.dumps(preview(inventory), indent=2))

if __name__ == "__main__":
    main()
