"""Source-only checks for the fail-closed preview root classifier.
Does not execute VB, resolve reparse points, verify Vault or authorize APPLY.
Run: python -m unittest discover -s tests/static -p 'test_property_refresh_roots_contract.py'
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "scripts/ilogic/experiments/BEEXCITED_PropertyRefreshRoots.iLogicVb"

class RootClassifierContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = "\n".join(line for line in SOURCE.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("'"))

    def test_version_and_single_entry(self):
        self.assertIn('ClassifierVersion As String = "0.1.0-preview"', self.code)
        self.assertEqual(self.code.count("Public Function ClassifyPreviewRoot("), 1)

    def test_explicit_fail_closed_states(self):
        for token in ("BlockedInvalidPath", "BlockedExternalLibrary", "BlockedOutsideApprovedRoot", "PreviewCandidateRequiresOwnershipVerification"):
            self.assertIn(token, self.code)

    def test_protected_precedes_approved_result(self):
        self.assertLess(self.code.index("Return RootDecision.BlockedExternalLibrary"), self.code.index("Return RootDecision.PreviewCandidateRequiresOwnershipVerification"))

    def test_boundary_and_case_guard(self):
        self.assertIn("root & Path.DirectorySeparatorChar", self.code)
        self.assertIn("StringComparison.OrdinalIgnoreCase", self.code)
        self.assertIn("Path.GetFullPath", self.code)

    def test_no_apply_or_vault_claim(self):
        for forbidden in ("ThisApplication", "Save2(", "SaveAs(", "CheckOut(", "File.Write", "MessageBox", "InputBox"):
            self.assertNotIn(forbidden, self.code)

if __name__ == "__main__":
    unittest.main()
