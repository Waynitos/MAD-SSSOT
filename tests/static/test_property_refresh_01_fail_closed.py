"""Offline safety regression for Property Refresh Test 01 (no Inventor required).

Run: python -m unittest tests/static/test_property_refresh_01_fail_closed.py
This is a source-level guard, NOT proof of Inventor/Vault runtime safety.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
RULE = ROOT / "scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"


class FailClosedContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = RULE.read_text(encoding="utf-8")

    def test_apply_is_rejected_before_discovery(self):
        source = self.source
        guard = source.index('If apply Then')
        rejection = source.index('Return', guard)
        discovery = source.index('Dim files As New')
        self.assertLess(guard, rejection)
        self.assertLess(rejection, discovery)
        self.assertIn('APPLY BLOCKED', source[guard:rejection])

    def test_no_revision_property_writes(self):
        self.assertNotRegex(self.source, r'(?im)^\s*Queue(?:Change|Prefix)\([^\n]*["\'](?:REVISION|REV)\b')

    def test_drawing_identity_requires_matching_old_prefix(self):
        source = self.source
        fn = source[source.index('Function PlanDrawingNumber('):source.index('End Function', source.index('Function PlanDrawingNumber('))]
        for expected in ('fileMatch.Success', 'propertyMatch.Success', 'fileMatch.Value, propertyMatch.Value', 'ReplaceLeadingProject(existingNumber, targetPrefix)'):
            self.assertIn(expected, fn)

    def test_no_automatic_vault_checkout_or_copy_design(self):
        source = self.source
        for forbidden in ('CheckOutFile(', 'SaveAs(', 'CopyDesign(', 'ReplaceReference('):
            self.assertNotIn(forbidden, source)

    def test_shared_core_not_yet_extracted(self):
        """Known qualification blocker: keep test explicit until architecture changes."""
        self.assertIn('Sub Main()', self.source)
        self.assertIn('Function EligibilityReason(', self.source)
        self.assertNotIn('ExecutePropertyRefresh(', self.source)


if __name__ == "__main__":
    unittest.main()
