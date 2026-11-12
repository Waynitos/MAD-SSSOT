"""SCS v2.2.34 offline Existing Target Repair plan gate.

Pure Python, standard library only. No Inventor/Vault access or writes.
Consumes a JSON snapshot exported by a future read-only Inventor collector.
This is a *preflight* only; passing cannot authorize mutation.
"""
import json
import os
import sys
from collections import Counter

REQUIRED = ("target", "source", "occurrences", "documents")
BLOCKERS = {
    "missing_provenance", "vault_unknown", "not_checked_out",
    "read_only", "dirty", "collision", "missing_file",
    "frame_identity_unknown", "frame_dependency_unknown",
    "reference_unresolved", "backup_unverified",
}

def canonical(path):
    if not isinstance(path, str) or not path.strip():
        return ""
    return os.path.normcase(os.path.normpath(path.strip())).casefold()

def validate(plan):
    errors = []
    if not isinstance(plan, dict):
        return ["BLOCK_INVALID_PLAN"]
    for key in REQUIRED:
        if key not in plan:
            errors.append("BLOCK_MISSING_" + key.upper())
    if errors:
        return errors
    target, source = canonical(plan["target"]), canonical(plan["source"])
    if not target or not source or target == source:
        errors.append("BLOCK_TARGET_SOURCE_IDENTITY")
    if not isinstance(plan["occurrences"], list) or not isinstance(plan["documents"], list):
        return errors + ["BLOCK_INVALID_COLLECTION"]
    paths = []
    for i, doc in enumerate(plan["documents"]):
        if not isinstance(doc, dict):
            errors.append("BLOCK_DOCUMENT_SCHEMA:" + str(i))
            continue
        path = canonical(doc.get("path"))
        if not path:
            errors.append("BLOCK_DOCUMENT_PATH:" + str(i))
        paths.append(path)
        for field in ("provenance", "vault_state", "read_only", "dirty", "exists", "frame_state", "backup_verified"):
            if field not in doc:
                errors.append("BLOCK_UNKNOWN_" + field.upper() + ":" + str(i))
        if not doc.get("provenance"):
            errors.append("BLOCK_MISSING_PROVENANCE:" + str(i))
        if doc.get("vault_state") != "checked_out_to_current_user":
            errors.append("BLOCK_VAULT_NOT_CONFIRMED:" + str(i))
        if doc.get("read_only") is not False:
            errors.append("BLOCK_READONLY_UNKNOWN_OR_TRUE:" + str(i))
        if doc.get("dirty") is not False:
            errors.append("BLOCK_DIRTY_UNKNOWN_OR_TRUE:" + str(i))
        if doc.get("exists") is not True:
            errors.append("BLOCK_FILE_MISSING_OR_UNKNOWN:" + str(i))
        if doc.get("frame_state") not in ("not_frame", "verified_associativity"):
            errors.append("BLOCK_FRAME_UNVERIFIED:" + str(i))
        if doc.get("backup_verified") is not True:
            errors.append("BLOCK_BACKUP_UNVERIFIED:" + str(i))
    for path, count in Counter(p for p in paths if p).items():
        if count > 1:
            errors.append("BLOCK_DUPLICATE_DOCUMENT:" + path)
    known = set(paths)
    for i, occ in enumerate(plan["occurrences"]):
        if not isinstance(occ, dict):
            errors.append("BLOCK_OCCURRENCE_SCHEMA:" + str(i))
            continue
        for field in ("parent", "current", "proposed", "identity_verified", "descriptor_verified"):
            if field not in occ:
                errors.append("BLOCK_UNKNOWN_" + field.upper() + ":" + str(i))
        parent, current, proposed = (canonical(occ.get(k)) for k in ("parent", "current", "proposed"))
        if not parent or not current or not proposed or parent not in known or proposed not in known:
            errors.append("BLOCK_OCCURRENCE_REFERENCE:" + str(i))
        if occ.get("identity_verified") is not True or occ.get("descriptor_verified") is not True:
            errors.append("BLOCK_REFERENCE_IDENTITY:" + str(i))
    if not plan.get("rollback_journal_verified"):
        errors.append("BLOCK_ROLLBACK_JOURNAL")
    if not plan.get("profiling_retained"):
        errors.append("BLOCK_PROFILING")
    # Even a structurally valid snapshot cannot prove current Vault state or a saved/reopened model.
    return sorted(set(errors))

def main():
    if len(sys.argv) != 2:
        print("usage: python existing_target_plan_gate.py snapshot.json", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as stream:
        plan = json.load(stream)
    blockers = validate(plan)
    print(json.dumps({"status": "BLOCKED" if blockers else "PREVIEW_STRUCTURALLY_VALID_NOT_AUTHORIZED",
                      "blockers": blockers}, indent=2))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
