"""Structural-only validation for v1 repair evidence. Never authorizes mutation.

A manifest is untrusted caller data. Even a clean result cannot certify Inventor,
Vault, producer identity, or a fresh execution-time readback.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import PureWindowsPath
import re

SCHEMA = "scs.existing-target-repair.evidence.v1"
EXTS = {".iam", ".ipt", ".idw", ".dwg", ".ipn"}
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def windows_key(value):
    if not isinstance(value, str) or not value:
        return None
    p = PureWindowsPath(value)
    if not p.is_absolute() or not p.drive or ".." in p.parts:
        return None
    return str(p).casefold()


def inside(path, root):
    p, r = windows_key(path), windows_key(root)
    return p is not None and r is not None and (p == r or p.startswith(r.rstrip("\\") + "\\"))


def validate(manifest):
    """Return deterministic blockers; no certificate or approval is issued."""
    errors = []
    if not isinstance(manifest, dict):
        return ["INVALID_MANIFEST"]
    if manifest.get("schema") != SCHEMA:
        errors.append("UNSUPPORTED_SCHEMA")
    target = manifest.get("target")
    root = target.get("root") if isinstance(target, dict) else None
    ga = target.get("top_ga") if isinstance(target, dict) else None
    if windows_key(root) is None or not inside(ga, root):
        errors.append("INVALID_TARGET")
    producer = manifest.get("producer")
    if not isinstance(producer, dict) or not producer.get("name") or not producer.get("version"):
        errors.append("MISSING_PRODUCER")
    # A producer label is never authenticated by the manifest.
    errors.append("PRODUCER_AUTHENTICATION_REQUIRED")
    captured = manifest.get("captured_at_utc")
    try:
        stamp = datetime.fromisoformat(captured.replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("not UTC")
        if stamp > datetime.now(timezone.utc):
            errors.append("FUTURE_SNAPSHOT")
    except (AttributeError, TypeError, ValueError):
        errors.append("INVALID_CAPTURE_TIME")
    documents = manifest.get("documents")
    edges = manifest.get("edges")
    frames = manifest.get("frame_generator")
    if not isinstance(documents, list) or not documents:
        errors.append("MISSING_DOCUMENTS")
        documents = []
    if not isinstance(edges, list):
        errors.append("INVALID_EDGES")
        edges = []
    if not isinstance(frames, list):
        errors.append("INVALID_FRAME_GENERATOR")
    identities, paths = [], []
    for index, doc in enumerate(documents):
        if not isinstance(doc, dict):
            errors.append(f"INVALID_DOCUMENT:{index}")
            continue
        identity, path = doc.get("identity"), doc.get("path")
        if not isinstance(identity, str) or not identity.strip():
            errors.append(f"MISSING_IDENTITY:{index}")
        else:
            identities.append(identity)
        if not inside(path, root):
            errors.append(f"DOCUMENT_OUTSIDE_TARGET:{index}")
        else:
            paths.append(windows_key(path))
        if not isinstance(path, str) or PureWindowsPath(path).suffix.casefold() not in EXTS:
            errors.append(f"UNSUPPORTED_DOCUMENT:{index}")
        if not isinstance(doc.get("sha256"), str) or not HEX64.fullmatch(doc["sha256"]):
            errors.append(f"MISSING_FINGERPRINT:{index}")
        if not isinstance(doc.get("size"), int) or isinstance(doc.get("size"), bool) or doc["size"] < 0:
            errors.append(f"INVALID_SIZE:{index}")
        if doc.get("discovery_errors") != []:
            errors.append(f"DOCUMENT_DISCOVERY_UNVERIFIED:{index}")
    if any(count > 1 for count in Counter(identities).values()):
        errors.append("DUPLICATE_IDENTITY")
    if any(count > 1 for count in Counter(paths).values()):
        errors.append("WINDOWS_PATH_COLLISION")
    if windows_key(ga) not in paths:
        errors.append("TOP_GA_NOT_IN_DOCUMENTS")
    known = set(identities)
    # Frame Generator evidence is not optional when records are supplied.
    # Structural references alone never establish Inventor-side integrity.
    if isinstance(frames, list):
        for index, frame in enumerate(frames):
            if not isinstance(frame, dict):
                errors.append(f"INVALID_FRAME_RECORD:{index}")
                continue
            required = ("frame_assembly_identity", "skeleton_identity",
                        "member_identity")
            if any(not isinstance(frame.get(field), str) or
                   frame[field] not in known for field in required):
                errors.append(f"UNRESOLVED_FRAME_RELATION:{index}")
            if frame.get("external_reference") is not False:
                errors.append(f"FRAME_EXTERNAL_REFERENCE_UNVERIFIED:{index}")
    for index, edge in enumerate(edges):
        if (not isinstance(edge, dict)
                or not isinstance(edge.get("parent_identity"), str)
                or not isinstance(edge.get("child_identity"), str)
                or edge["parent_identity"] not in known
                or edge["child_identity"] not in known):
            errors.append(f"UNRESOLVED_EDGE:{index}")
        elif (edge.get("resolved") is not True
              or not isinstance(edge.get("discovery_api"), str)
              or not edge["discovery_api"].strip()):
            errors.append(f"UNCERTIFIED_EDGE:{index}")
    discovery = manifest.get("discovery")
    if not isinstance(discovery, dict) or discovery.get("complete") is not True or discovery.get("errors") != []:
        errors.append("DISCOVERY_INCOMPLETE")
    profiler = manifest.get("profiler")
    if (not isinstance(profiler, dict)
            or profiler.get("baseline") != "v2.2.33"
            or not isinstance(profiler.get("checkpoints"), list)):
        errors.append("PROFILER_EVIDENCE_MISSING")
    vault = manifest.get("vault")
    if not isinstance(vault, dict) or vault.get("clearance") != "verified" or not vault.get("identity"):
        errors.append("VAULT_UNVERIFIED")
    # Even verified-looking JSON is untrusted; execution requires independent readback.
    errors.extend(["INVENTOR_READBACK_REQUIRED", "VAULT_READBACK_REQUIRED", "EXECUTION_PREFLIGHT_REQUIRED"])
    return sorted(set(errors))
