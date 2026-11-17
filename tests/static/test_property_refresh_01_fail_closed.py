"""Source-only fail-closed regression for Property Refresh Test 01.

Run: python -m unittest tests/static/test_property_refresh_01_fail_closed.py
These are lexical contracts, not VB compilation or Inventor/Vault validation.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "scripts/ilogic/experiments"
RULE = EXPERIMENTS / "BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"
PURE = EXPERIMENTS / "BEEXCITED_PropertyRefreshPure.iLogicVb"


class FailClosedContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = RULE.read_text(encoding="utf-8-sig")
        cls.pure = PURE.read_text(encoding="utf-8-sig")

    def test_apply_rejected_before_discovery(self):
        source = self.wrapper
        guard = source.index("If apply Then")
        rejection = source.index("Return", guard)
        discovery = source.index("BEEXCITED_PropertyRefreshDiscovery.Discover")
        self.assertLess(guard, rejection)
        self.assertLess(rejection, discovery)
        self.assertIn("APPLY BLOCKED", source[guard:rejection])

    def test_no_property_mutation_or_save_in_preview(self):
        source = self.wrapper
        for forbidden in (r"\.Value\s*=", r"\bSave2\s*\(", r"\bSaveAs\s*\(",
                          r"\bCheckOutFile\s*\(", r"\bCopyDesign\s*\("):
            with self.subTest(forbidden=forbidden):
                self.assertNotRegex(source, forbidden)

    def test_drawing_identity_delegated_to_pure_core(self):
        self.assertIn("BEEXCITED_PropertyRefreshPure.PlanExistingDrawingProperty(", self.wrapper)
        for expected in ("fileMatch.Success", "propertyMatch.Success"):
            self.assertNotIn(expected, self.wrapper)
        self.assertIn("PlanDrawingNumber(existingValue:=existingDrawingNumber", self.pure)
        self.assertIn("fileBaseName:=filenameStem", self.pure)
        self.assertIn("String.Equals(existingValue.Substring(0, 7), fileBaseName.Substring(0, 7)", self.pure)

    def test_shared_core_and_fail_closed_boundaries(self):
        for required in (
            "BEEXCITED_PropertyRefreshPure.PlanExistingModelProperty(",
            "BEEXCITED_PropertyRefreshEligibility.ClassifyPreview(",
            "BEEXCITED_PropertyRefreshDiscovery.Discover",
            "BEEXCITED_PropertyRefreshAudit.",
            "Catch ex As Exception",
            "PREVIEW ABORTED",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.wrapper)

    def test_unverified_drawing_mapping_and_no_revision_reset(self):
        self.assertIn("UNVERIFIED drawing/title-block mapping", self.wrapper)
        self.assertNotRegex(self.wrapper, r'(?im)^\s*\.PropertyName\s*=\s*"(?:REVISION|REV)"')


if __name__ == "__main__":
    unittest.main()
