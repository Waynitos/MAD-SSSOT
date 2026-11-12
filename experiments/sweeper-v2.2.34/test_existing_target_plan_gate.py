"""Synthetic fail-closed tests. Run: python -m unittest discover -s experiments/sweeper-v2.2.34 -p 'test_existing_target_plan_gate.py'"""
import unittest
from existing_target_plan_gate import validate

def sample():
    return {
        "target": "C:/new/ga.iam", "source": "C:/old/ga.iam",
        "documents": [{"path": "C:/new/ga.iam", "provenance": "C:/old/ga.iam",
                       "vault_state": "checked_out_to_current_user",
                       "read_only": False, "dirty": False, "exists": True,
                       "frame_state": "not_frame", "backup_verified": True},
                      {"path": "C:/new/part.ipt", "provenance": "C:/old/part.ipt",
                       "vault_state": "checked_out_to_current_user", "read_only": False,
                       "dirty": False, "exists": True, "frame_state": "not_frame",
                       "backup_verified": True}],
        "occurrences": [{"parent": "C:/new/ga.iam", "current": "C:/old/part.ipt", "proposed": "C:/new/part.ipt", "identity_verified": True, "descriptor_verified": True}], "rollback_journal_verified": True, "profiling_retained": True,
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

    def test_windows_slash_case_duplicate_blocked(self):
        p = sample()
        p["documents"].append(dict(p["documents"][0], path=r"c:\\NEW\\GA.IAM"))
        self.assertTrue(any("DUPLICATE" in x for x in validate(p)))

    def test_relative_document_blocked(self):
        p = sample()
        p["documents"][0]["path"] = r"..\\new\\ga.iam"
        self.assertTrue(any("NONABSOLUTE_DOCUMENT" in x for x in validate(p)))

    def test_relative_roots_blocked(self):
        p = sample()
        p["target"] = r"..\\new\\ga.iam"
        self.assertIn("BLOCK_NONABSOLUTE_ROOT", validate(p))

class RepairCompletenessTests(unittest.TestCase):
    def test_empty_repair_is_blocked(self):
        p = sample(); p["occurrences"] = []
        self.assertIn("BLOCK_NO_REPAIR_OCCURRENCES", validate(p))
    def test_target_must_be_in_inventory(self):
        p = sample(); p["target"] = "C:/new/missing.iam"
        self.assertIn("BLOCK_TARGET_NOT_IN_DOCUMENTS", validate(p))
    def test_noop_replacement_blocked(self):
        p = sample(); p["occurrences"][0]["current"] = "C:/new/part.ipt"
        self.assertIn("BLOCK_NOOP_OCCURRENCE:0", validate(p))
    def test_self_reference_blocked(self):
        p = sample(); p["occurrences"][0]["proposed"] = "C:/new/ga.iam"
        self.assertIn("BLOCK_SELF_REFERENCE:0", validate(p))
