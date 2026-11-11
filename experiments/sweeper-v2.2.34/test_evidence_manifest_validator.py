"""Offline structural checks; no Inventor/Vault execution."""
import unittest
from evidence_manifest_validator import validate


def sample():
    return {
        "schema": "scs.existing-target-repair.evidence.v1",
        "producer": {"name": "untrusted", "version": "1"},
        "captured_at_utc": "2026-01-01T00:00:00Z",
        "target": {"root": r"C:\\Copy", "top_ga": r"C:\\Copy\\GA.iam"},
        "documents": [{"identity": "ga", "path": r"C:\\Copy\\GA.iam",
                       "sha256": "a" * 64, "size": 1, "discovery_errors": []}],
        "edges": [], "frame_generator": [],
        "discovery": {"complete": True, "errors": []},
        "vault": {"identity": "untrusted", "clearance": "verified"},
    }


class ManifestTests(unittest.TestCase):
    def test_even_perfect_assertions_never_authorize(self):
        blockers = validate(sample())
        self.assertIn("PRODUCER_AUTHENTICATION_REQUIRED", blockers)
        self.assertIn("INVENTOR_READBACK_REQUIRED", blockers)
        self.assertIn("VAULT_READBACK_REQUIRED", blockers)
        self.assertIn("EXECUTION_PREFLIGHT_REQUIRED", blockers)

    def test_case_insensitive_collision(self):
        m = sample()
        m["documents"].append(dict(m["documents"][0], identity="duplicate", path=r"C:\\COPY\\ga.IAM"))
        self.assertIn("WINDOWS_PATH_COLLISION", validate(m))

    def test_escape_and_unresolved_edge(self):
        m = sample()
        m["documents"][0]["path"] = r"C:\\Copy\\..\\Outside\\GA.iam"
        m["edges"] = [{"parent_identity": "ga", "child_identity": "missing"}]
        blockers = validate(m)
        self.assertIn("DOCUMENT_OUTSIDE_TARGET:0", blockers)
        self.assertIn("UNRESOLVED_EDGE:0", blockers)

    def test_malformed_edge_identifiers_fail_closed_without_crashing(self):
        for malformed in ([], {}, 7, None):
            with self.subTest(malformed=malformed):
                m = sample()
                m["edges"] = [{"parent_identity": malformed, "child_identity": "ga",
                               "resolved": True, "discovery_api": "Inventor"}]
                self.assertIn("UNRESOLVED_EDGE:0", validate(m))

    def test_discovery_api_requires_nonempty_string(self):
        for malformed in ([], {}, "   "):
            with self.subTest(malformed=malformed):
                m = sample()
                m["edges"] = [{"parent_identity": "ga", "child_identity": "ga",
                               "resolved": True, "discovery_api": malformed}]
                self.assertIn("UNCERTIFIED_EDGE:0", validate(m))

    def test_invalid_evidence(self):
        m = sample()
        m["documents"][0]["sha256"] = "bad"
        m["discovery"]["complete"] = False
        m["vault"]["clearance"] = "unknown"
        blockers = validate(m)
        for expected in ("MISSING_FINGERPRINT:0", "DISCOVERY_INCOMPLETE", "VAULT_UNVERIFIED"):
            self.assertIn(expected, blockers)


if __name__ == "__main__":
    unittest.main()
