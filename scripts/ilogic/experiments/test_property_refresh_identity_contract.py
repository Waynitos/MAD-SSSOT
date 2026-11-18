"""Static contract regression for pure Property Refresh identity gate.
Run: python -m unittest scripts/ilogic/experiments/test_property_refresh_identity_contract.py
This is NOT VB compilation or Inventor/Vault runtime validation.
"""
import pathlib
import re
import unittest

SOURCE = pathlib.Path(__file__).with_name("BEEXCITED_PropertyRefreshIdentity.iLogicVb")


class IdentityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = SOURCE.read_text(encoding="utf-8")

    def test_single_public_decision_entry(self):
        self.assertEqual(len(re.findall(r"Public Function EvaluateApplyIdentity\s*\(", self.code, re.I)), 1)

    def test_missing_and_ambiguous_evidence_denied(self):
        self.assertRegex(self.code, r"Not evidence\.ResolutionSucceeded")
        self.assertRegex(self.code, r"evidence\.IsReparseAmbiguous")
        self.assertRegex(self.code, r"evidence\.ResolvedProtectedRoots Is Nothing")
        self.assertRegex(self.code, r"Return IdentityReason\.DenyMissingEvidence")

    def test_stable_file_identity_rechecked(self):
        self.assertIn("evidence.StableFileId", self.code)
        self.assertIn("evidence.RecheckedFileId", self.code)
        self.assertIn("IdentityReason.DenyChangedIdentity", self.code)

    def test_source_and_external_protected_roots_denied(self):
        self.assertIn("If IsUnder(candidate, source)", self.code)
        self.assertIn("If Not IsUnder(candidate, target)", self.code)
        self.assertIn("If IsUnder(candidate, protectedRoot)", self.code)

    def test_prefix_boundary_not_plain_startswith(self):
        self.assertIn("root & separator", self.code)
        self.assertIn("StringComparison.OrdinalIgnoreCase", self.code)

    def test_no_mutation_or_ui_in_pure_gate(self):
        forbidden = (r"\.Save(?:As|2)?\s*\(", r"\.PropertySets\b",
                     r"MessageBox\.", r"InputBox\s*\(", r"Vault\.",
                     r"File\.Write", r"File\.Delete", r"File\.Move")
        for pattern in forbidden:
            self.assertNotRegex(self.code, pattern)

    def test_eligibility_not_apply_authorization(self):
        self.assertIn("EligibleIdentityOnly", self.code)
        self.assertNotRegex(self.code, r"\bApplyAuthorized\b")


if __name__ == "__main__":
    unittest.main()
