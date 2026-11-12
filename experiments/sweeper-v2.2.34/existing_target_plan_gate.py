"""SCS v2.2.34 offline Existing Target Repair plan gate.

Pure Python, standard library only. No Inventor/Vault access or writes.
Consumes a JSON snapshot exported by a future read-only Inventor collector.
This is a *preflight* only; passing cannot authorize mutation.
"""
import json
import ntpath
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
    return ntpath.normcase(ntpath.normpath(path.strip())).casefold()

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
    # Windows path comparisons must not depend on the host running the offline gate.
    if not ntpath.isabs(target) or not ntpath.isabs(source):
        errors.append("BLOCK_NONABSOLUTE_ROOT")
    for i, doc in enumerate(plan["documents"]):
        if not isinstance(doc, dict):
            errors.append("BLOCK_DOCUMENT_SCHEMA:" + str(i))
            continue
        path = canonical(doc.get("path"))
        if not path:
            errors.append("BLOCK_DOCUMENT_PATH:" + str(i))
        paths.append(path)
        if path and not ntpath.isabs(path):
            errors.append("BLOCK_NONABSOLUTE_DOCUMENT:" + str(i))
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
    provenance = {canonical(d.get("path")): canonical(d.get("provenance")) for d in plan["documents"] if isinstance(d, dict)}
    occurrence_keys = set()
    if target not in known:
        errors.append("BLOCK_TARGET_NOT_IN_DOCUMENTS")
    if not plan["occurrences"]:
        errors.append("BLOCK_NO_REPAIR_OCCURRENCES")
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
        if any(p and not ntpath.isabs(p) for p in (parent, current, proposed)):
            errors.append("BLOCK_NONABSOLUTE_OCCURRENCE:" + str(i))
        if current not in known and current not in set(provenance.values()):
            errors.append("BLOCK_CURRENT_NOT_IN_INVENTORY_OR_PROVENANCE:" + str(i))
        if proposed in provenance and provenance[proposed] != current:
            errors.append("BLOCK_PROVENANCE_MISMATCH:" + str(i))
        occurrence_key = (parent, current, proposed)
        if occurrence_key in occurrence_keys:
            errors.append("BLOCK_DUPLICATE_OCCURRENCE:" + str(i))
        occurrence_keys.add(occurrence_key)
        if current == proposed and current:
            errors.append("BLOCK_NOOP_OCCURRENCE:" + str(i))
        if parent == proposed and parent:
            errors.append("BLOCK_SELF_REFERENCE:" + str(i))
        if occ.get("identity_verified") is not True or occ.get("descriptor_verified") is not True:
            errors.append("BLOCK_REFERENCE_IDENTITY:" + str(i))
    # Proposed parent->child edges must never introduce an assembly dependency cycle.
    # Fail closed even when all individual descriptors and file paths look valid.
    graph = {}
    for occ in plan["occurrences"]:
        if not isinstance(occ, dict):
            continue
        parent, proposed = canonical(occ.get("parent")), canonical(occ.get("proposed"))
        if parent and proposed and parent in known and proposed in known:
            graph.setdefault(parent, set()).add(proposed)
    # Iterative DFS avoids Python recursion limits on large assembly graphs.
    # 0 = unseen, 1 = active, 2 = complete.
    states = {}
    cyclic = False
    for root_node in graph:
        if states.get(root_node, 0):
            continue
        states[root_node] = 1
        stack = [(root_node, iter(graph.get(root_node, ())))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                states[node] = 2
                stack.pop()
                continue
            state = states.get(child, 0)
            if state == 1:
                cyclic = True
                break
            if state == 0:
                states[child] = 1
                stack.append((child, iter(graph.get(child, ()))))
        if cyclic:
            break
    if cyclic:
        errors.append("BLOCK_PROPOSED_REFERENCE_CYCLE")
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
