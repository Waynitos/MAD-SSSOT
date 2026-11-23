"""Offline source-contract checks for the pure Property Refresh APPLY evidence gate.
Run: python -m unittest tests/static/test_property_refresh_01_apply_evidence_gate.py
No Inventor runtime or VB compilation is implied.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/ilogic/experiments/BEEXCITED_PropertyRefreshApplyGate.iLogicVb"

class ApplyEvidenceSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_no_io_inventor_or_ui(self):
        for forbidden in ("Inventor.Document", "SaveAs(", ".Save(", "InputBox(", "MessageBox.", "File.Write", "CopyDesign"):
            self.assertNotIn(forbidden.lower(), self.source.lower())

    def test_every_safety_evidence_is_fail_closed(self):
        fields = (
            "ExplicitApplyConfirmed", "ImmutablePlanMatches", "SavedDocument",
            "DocumentClean", "CanonicalPhysicalIdentityVerified",
            "ApprovedProjectRootVerified", "NotExternalProtectedLibrary",
            "FileWritable", "VaultCheckoutOwnedVerified", "PropertyMappingVerified",
            "OriginalValuesMatchSnapshot", "ApprovedPopulatedFieldsOnly",
            "ExternalComSupervisorReady", "IndependentPersistedReadbackReady",
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertRegex(self.source, rf"Public Property {field} As Boolean")
                self.assertRegex(self.source, rf"If Not evidence\.{field} Then Return Deny\(")

    def test_no_mutation_authority(self):
        self.assertIn("AllowedToProceedToRevalidation", self.source)
        self.assertNotIn("AllowedToWrite", self.source)
        self.assertIn("NOT write authorization", self.source)

    def test_null_evidence_denied(self):
        self.assertIn('If evidence Is Nothing Then Return Deny("Missing evidence")', self.source)

if __name__ == "__main__":
    unittest.main()
