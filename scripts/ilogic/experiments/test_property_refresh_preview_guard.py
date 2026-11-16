"""Fail-closed source qualification for PROPERTY REFRESH TEST 01.

Run: python -m unittest scripts/ilogic/experiments/test_property_refresh_preview_guard.py
Static source checks only: NOT Inventor compilation, Vault verification, or runtime testing.
"""
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
WRAPPER = HERE / "BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"
ELIGIBILITY = HERE / "BEEXCITED_PropertyRefreshEligibility.iLogicVb"


class PropertyRefreshPreviewGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = WRAPPER.read_text(encoding="utf-8")
        cls.eligibility = ELIGIBILITY.read_text(encoding="utf-8")

    def test_apply_explicitly_blocked(self):
        self.assertRegex(self.wrapper, r"(?is)If apply Then\s*MessageBox\.Show\(\"APPLY BLOCKED.*?Return\s*End If")

    def test_no_property_mutation_or_save(self):
        self.assertNotRegex(self.wrapper, r"(?i)\.Save2?\s*\(")
        self.assertNotRegex(self.wrapper, r"(?i)\.PropertySets.*?\.Value\s*=")
        self.assertNotRegex(self.wrapper, r"(?i)\.SaveAs\s*\(")

    def test_delegates_shared_functions(self):
        for name in ("BEEXCITED_PropertyRefreshPure.", "BEEXCITED_PropertyRefreshDiscovery.",
                     "BEEXCITED_PropertyRefreshEligibility.ClassifyPreview",
                     "BEEXCITED_PropertyRefreshAudit.AppendRecord"):
            with self.subTest(name=name):
                self.assertIn(name, self.wrapper)

    def test_protected_roots_fail_closed(self):
        self.assertIn("If protectedRoots.Count = 0 Then", self.wrapper)
        self.assertIn("If protectedList.Count = 0 Then Return EligibilityDecision.BlockedMissingOrInvalid", self.eligibility)
        self.assertIn("BlockedProtectedLibrary", self.eligibility)

    def test_drawing_mapping_unverified(self):
        self.assertIn("UNVERIFIED drawing/title-block mapping", self.wrapper)
        self.assertIn("DRAWING_NUMBER", self.wrapper)
        self.assertNotIn("DRAWING_NUMBER VERIFIED", self.wrapper)

    def test_dirty_documents_skipped(self):
        self.assertIn("If active.Dirty Then", self.wrapper)
        self.assertIn("If doc.Dirty Then", self.wrapper)

    def test_no_copy_design_or_checkout(self):
        self.assertNotRegex(self.wrapper, r"(?i)\b(?:CopyDesign|CheckOutFile|AcquireFiles)\s*\(")

    def test_audit_never_claims_persisted_verification(self):
        self.assertIn('entry.Verification = "NOT-PERSISTED-NOT-VERIFIED"', self.wrapper)


if __name__ == "__main__":
    unittest.main()
