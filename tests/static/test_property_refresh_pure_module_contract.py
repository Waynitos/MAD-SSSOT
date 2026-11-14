"""Offline structural contract for BEEXCITED_PropertyRefreshPure.

Run: python -m unittest tests/static/test_property_refresh_pure_module_contract.py
These checks inspect source only; they do not compile or execute VB/iLogic.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/ilogic/experiments/BEEXCITED_PropertyRefreshPure.iLogicVb"


class PureModuleContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.code = "\n".join(
            line for line in cls.source.splitlines()
            if not line.lstrip().startswith("'")
        )

    def test_public_module_and_version(self):
        self.assertRegex(self.code, r"Public Module BEEXCITED_PropertyRefreshPure")
        self.assertRegex(self.code, r'EngineVersion As String = "0\.1\.0-preview"')

    def test_expected_entry_points_are_unique(self):
        for name in (
            "NormalizeProjectPrefix",
            "ReplaceLeadingProjectPrefix",
            "PlanDrawingNumber",
            "PlanExistingModelProperty",
        ):
            self.assertEqual(
                len(re.findall(r"Public Function\s+" + name + r"\s*\(", self.code)),
                1, name,
            )

    def test_strict_prefix_and_suffix_preservation(self):
        self.assertIn('^PJ[0-9]{5}$', self.code)
        self.assertIn('^PJ[0-9]{5}-', self.code)
        self.assertIn('original.Substring(7)', self.code)
        self.assertIn('existingValue.Substring(7)', self.code)

    def test_drawing_identity_cross_check(self):
        self.assertIn('fileBaseName.Substring(0, 7)', self.code)
        self.assertIn('existingValue.Substring(0, 7)', self.code)
        self.assertIn('StringComparison.OrdinalIgnoreCase', self.code)

    def test_no_inventor_ui_or_write_api(self):
        for forbidden in (
            r"\bThisApplication\b", r"\bInventor\.\w+", r"\biLogicVb\b",
            r"\bMessageBox\b", r"\bInputBox\b", r"\bSaveAs\s*\(",
            r"\bSave2\s*\(", r"\bFile\.Write\w*\s*\(",
            r"\bPropertySets\b", r"\bCopyDesign\b",
        ):
            self.assertNotRegex(self.code, forbidden)

    def test_no_apply_claim(self):
        self.assertNotRegex(self.code, r"(?i)Public\s+(Sub|Function)\s+ExecutePropertyRefresh\b")
        self.assertNotRegex(self.code, r"(?i)\bCheckOut\s*\(")


if __name__ == "__main__":
    unittest.main()
