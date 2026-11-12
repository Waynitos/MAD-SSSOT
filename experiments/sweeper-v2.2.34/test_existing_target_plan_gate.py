"""Synthetic fail-closed tests. Run: python -m unittest discover -s experiments/sweeper-v2.2.34 -p 'test_existing_target_plan_gate.py'"""
import unittest
from existing_target_plan_gate import validate

def sample():
    return {
        "target": "C:/new/ga.iam", "source": "C:/old/ga.iam",
        "documents": [{"path": "C:/new/ga.iam", "provenance": "C:/old/ga.iam",
                       "vault_state": "checked_out_to_current_user",
                       "read_only": False, "dirty": False, "exists": True,
                       "frame_state": "not_frame", "backup_verified": True}],
        "occurrences": [], "rollback_journal_verified": True, "profiling_retained": True,
    }

class GateTests(unittest.TestCase):
    def test_structural_example(self):
        self.assertEqual(validate(sample()), [])
    def test_missing_vault_is_blocked(self):
        p = sample(); del p["documents"][0]["vault_state"]
        self.assertTrue(any("VAULT" in x for x in validate(p)))
    def test_frame_unknown_is_blocked(self):
        p = sample(); p["documents"][0]["frame_state"] = "unknown"
        self.assertTrue(any("FRAME" in x for x in validate(p)))
    def test_readonly_blocked(self):
        p = sample(); p["documents"][0]["read_only"] = True
        self.assertTrue(any("READONLY" in x for x in validate(p)))
    def test_duplicate_paths_blocked(self):
        p = sample(); p["documents"].append(dict(p["documents"][0]))
        self.assertTrue(any("DUPLICATE" in x for x in validate(p)))
    def test_unknown_occurrence_identity_blocked(self):
        p = sample(); p["occurrences"].append({"parent": "C:/new/ga.iam", "current": "C:/old/x.ipt", "proposed": "C:/new/x.ipt"})
        self.assertTrue(any("IDENTITY" in x for x in validate(p)))
    def test_no_rollback_blocked(self):
        p = sample(); p["rollback_journal_verified"] = False
        self.assertIn("BLOCK_ROLLBACK_JOURNAL", validate(p))
    def test_same_source_target_blocked(self):
        p = sample(); p["source"] = "c:/new/ga.iam"
        self.assertIn("BLOCK_TARGET_SOURCE_IDENTITY", validate(p))
