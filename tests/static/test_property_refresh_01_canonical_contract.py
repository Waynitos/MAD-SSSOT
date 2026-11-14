"""Source-level regression for canonical Property Refresh planning contracts.
Run: python -m unittest tests/static/test_property_refresh_01_canonical_contract.py
No Inventor/Vault runtime or VB compilation is performed.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PURE = ROOT / "scripts/ilogic/experiments/BEEXCITED_PropertyRefreshPure.iLogicVb"

class CanonicalPlannerSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PURE.read_text(encoding="utf-8-sig")

    def test_single_typed_drawing_entry(self):
        self.assertEqual(1, len(re.findall(r"(?im)^\s*Public Function PlanExistingDrawingProperty\(", self.source)))
        self.assertRegex(self.source, r"(?is)PlanDrawingNumber\(existingValue:=existingDrawingNumber,\s*fileBaseName:=filenameStem,\s*proposed:=targetProjectPrefix\)")

    def test_drawing_property_scope_and_no_revision_reset(self):
        self.assertIn('.PropertyName = "DRAWING_NUMBER"', self.source)
        self.assertIn('.PropertySetName = "Inventor User Defined Properties"', self.source)
        self.assertNotRegex(self.source, r'(?im)^\s*\.PropertyName\s*=\s*"REVISION"')

    def test_pure_planner_has_no_mutating_com_or_ui(self):
        for forbidden in (r"\bMessageBox\b", r"\bInputBox\b", r"\bSave2\s*\(", r"\bDocuments\.Open\b", r"\bThisApplication\b", r"\bPropertySets\.Item\b"):
            with self.subTest(forbidden=forbidden):
                self.assertNotRegex(self.source, forbidden)

    def test_prefix_requires_hyphen_and_preserves_suffix(self):
        self.assertIn('^PJ[0-9]{5}-', self.source)
        self.assertIn('original.Substring(7)', self.source)
        self.assertIn('existingValue.Substring(7)', self.source)

    def test_unchanged_returns_nothing(self):
        self.assertRegex(self.source, r"(?is)PlanExistingDrawingProperty\(.*?If String.Equals\(existingDrawingNumber, nextValue, StringComparison.Ordinal\) Then Return Nothing")

if __name__ == "__main__":
    unittest.main()
