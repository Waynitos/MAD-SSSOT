"""Offline, fail-closed preview gate for Existing Target Repair.
No Inventor automation, renames, writes to CAD files, or Vault operations.
Input is a JSON inventory produced by a separately verified discovery stage.
"""
import json
import os
import sys
import re
from collections import defaultdict
from pathlib import Path
from evidence_manifest_validator import validate as validate_evidence_manifest

EXTENSIONS = {".iam", ".ipt", ".idw", ".dwg", ".ipn"}
RESERVED = re.compile(r'^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$', re.I)

def key(path):
    return os.path.abspath(path).replace('\\', '/').casefold()

def valid_stem(stem):
    return (bool(stem) and not stem.endswith(('.', ' '))
            and not any(ord(c) < 32 or ord(c) == 127 for c in stem)
            and not any(c in stem for c in '<>:"/\\|?*')
            and not RESERVED.match(stem))

def under_root(path, root):
    p, r = key(path), key(root)
    real_p, real_r = key(os.path.realpath(path)), key(os.path.realpath(root))
    try:
        return os.path.commonpath([p, r]) == r and os.path.commonpath([real_p, real_r]) == real_r
    except ValueError:
        return False

def preview(inventory):
    if not isinstance(inventory, dict):
        raise ValueError("Inventory must be an object")
    target_root = inventory.get("target_root")
    if not isinstance(target_root, str) or not target_root.strip():
        raise ValueError("target_root must be a nonempty string")
    if not os.path.isabs(target_root):
        raise ValueError("target_root must be absolute")
    entries = inventory.get("files")
    if not isinstance(entries, list):
        raise ValueError("files must be an array")
    for index, item in enumerate(entries):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"].strip():
            raise ValueError("Invalid file record at index " + str(index))
        if not os.path.isabs(item["path"]):
            raise ValueError("File path must be absolute at index " + str(index))
    root = os.path.abspath(target_root)
    substitutions = inventory.get("substitutions")
    if not isinstance(substitutions, list) or len(substitutions) > 5:
        raise ValueError("Expected at most five substitutions")
    if any(not isinstance(x, list) or len(x) != 2 or not all(isinstance(y, str) for y in x) or not x[0] for x in substitutions):
        raise ValueError("Each substitution must be [nonempty search, replacement]")
    # Untrusted manifest assertions are validated structurally and never grant approval.
    # The preview is still usable without one, but explicitly reports missing evidence.
    manifest = inventory.get("evidence_manifest")
    blockers = (validate_evidence_manifest(manifest) if manifest is not None
                else ["EVIDENCE_MANIFEST_MISSING"])
    planned = []
    entries = inventory["files"]
    if not entries:
        blockers.append("EMPTY_INVENTORY")
    if inventory.get("discovery_complete") is not True:
        blockers.append("DISCOVERY_NOT_CERTIFIED")
    if inventory.get("reverse_references_complete") is not True:
        blockers.append("REVERSE_REFERENCES_NOT_CERTIFIED")
    if inventory.get("frame_generator_verified") is not True:
        blockers.append("FRAME_GENERATOR_NOT_VERIFIED")
    if inventory.get("vault_clearance_verified") is not True:
        blockers.append("VAULT_CLEARANCE_NOT_VERIFIED")
    if inventory.get("profiling_available") is not True:
        blockers.append("PROFILING_NOT_AVAILABLE")
    # Snapshot directory entries using Windows-style case-insensitive keys, even
    # when this offline preview is executed on a case-sensitive host.
    # A failed scan is a blocker, never evidence that the directory is empty.
    directory_entries = {}
    directories = {os.path.dirname(os.path.abspath(item["path"])) for item in entries}
    for directory in directories:
        try:
            names = os.listdir(directory)
            folded = {}
            for name in names:
                folded.setdefault(name.casefold(), []).append(name)
            for collisions in folded.values():
                if len(collisions) > 1:
                    blockers.append("AMBIGUOUS_WINDOWS_DIRECTORY_ENTRY:" + directory + ":" + " | ".join(sorted(collisions)))
            directory_entries[key(directory)] = folded
        except OSError:
            blockers.append("DESTINATION_DIRECTORY_UNREADABLE:" + directory)
    destinations = defaultdict(list)
    source_keys = {key(os.path.abspath(e["path"])) for e in entries}
    seen = set()
    for item in entries:
        src = os.path.abspath(item["path"])
        ext = Path(src).suffix.lower()
        if not under_root(src, root):
            blockers.append("OUTSIDE_ROOT_OR_SYMLINK_ESCAPE:" + src)
        if os.path.islink(src):
            blockers.append("SYMLINK_SOURCE:" + src)
        if ext not in EXTENSIONS:
            blockers.append("UNSUPPORTED_EXTENSION:" + src)
        source_key = key(src)
        if source_key in seen:
            blockers.append("DUPLICATE_SOURCE:" + src)
        seen.add(source_key)
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
        if not valid_stem(newstem):
            blockers.append("INVALID_TARGET_NAME:" + src)
        dst = os.path.join(os.path.dirname(src), newstem + Path(src).suffix)
        destinations[key(dst)].append(src)
        if not under_root(dst, root):
            blockers.append("DESTINATION_OUTSIDE_ROOT:" + dst)
        if src != dst and key(src) == key(dst):
            # Case-only renames need a separately designed Windows/Inventor lifecycle.
            blockers.append("CASE_ONLY_RENAME_UNSUPPORTED:" + src)
        if key(src) != key(dst):
            names = directory_entries.get(key(os.path.dirname(dst)))
            if names is None:
                blockers.append("DESTINATION_DIRECTORY_UNREADABLE:" + os.path.dirname(dst))
            elif os.path.basename(dst).casefold() in names:
                blockers.append("DESTINATION_EXISTS:" + dst)
            elif os.path.lexists(dst):
                blockers.append("DESTINATION_EXISTS:" + dst)
        if key(src) != key(dst) and key(dst) in source_keys:
            blockers.append("DESTINATION_IS_SOURCE:" + dst)
        planned.append({"source": src, "destination": dst, "changed": src != dst})
    for sources in destinations.values():
        if len(sources) > 1:
            blockers.append("DESTINATION_COLLISION:" + " | ".join(sources))
    if planned and not any(item["changed"] for item in planned):
        blockers.append("NO_EFFECTIVE_RENAMES")
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
