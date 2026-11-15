"""Fail-closed source architecture gates for PROPERTY REFRESH TEST 01.
Run: python -m unittest tests/static/test_property_refresh_01_shared_core_gate.py
Expected to FAIL until the standalone uses the canonical engine.
These tests do not compile VB or validate Inventor/Vault.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "scripts/ilogic/experiments"
STANDALONE = EXPERIMENT / "BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb"
CANONICAL = EXPERIMENT / "BEEXCITED_PropertyRefreshPure.iLogicVb"

class SharedCoreGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = STANDALONE.read_text(encoding="utf-8-sig")
        cls.core = CANONICAL.read_text(encoding="utf-8-sig")

    def test_canonical_planners_exist(self):
        for method in ("PlanExistingModelProperty", "PlanExistingDrawingProperty"):
            with self.subTest(method=method):
                self.assertRegex(self.core, rf"(?im)^\s*Public Function {method}\(")

    def test_wrapper_calls_both_canonical_planners(self):
        for method in ("PlanExistingModelProperty", "PlanExistingDrawingProperty"):
            with self.subTest(method=method):
                self.assertIn("BEEXCITED_PropertyRefreshPure." + method + "(", self.wrapper)

    def test_wrapper_does_not_duplicate_prefix_or_drawing_planning(self):
        for method in ("PlanDrawingNumber", "ReplaceLeadingProject", "QueuePrefix"):
            with self.subTest(method=method):
                self.assertNotRegex(self.wrapper, rf"(?im)^\s*(?:Private|Public)?\s*(?:Function|Sub)\s+{method}\(")

    def test_apply_is_fail_closed_until_runtime_gates(self):
        self.assertRegex(self.wrapper, r"(?is)If apply Then\s*MessageBox\.Show\(\"APPLY BLOCKED")
        self.assertRegex(self.wrapper, r"(?is)If apply Then\s*MessageBox\.Show\(.*?\)\s*Return")

    def test_canonical_does_not_depend_on_copy_design_or_ui(self):
        for forbidden in (r"\bThisApplication\b", r"\bMessageBox\b",
                          r"\bInputBox\b", r"\bSaveAs\b",
                          r"\bDocuments\.Open\b"):
            with self.subTest(forbidden=forbidden):
                self.assertNotRegex(self.core, forbidden)

if __name__ == "__main__":
    unittest.main()
