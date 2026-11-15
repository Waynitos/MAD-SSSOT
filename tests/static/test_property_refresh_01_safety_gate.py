"""Fail-closed safety gates for Property Refresh 01; source checks only.

Run: python -m unittest tests/static/test_property_refresh_01_safety_gate.py
Expected RED until authoritative ownership, Vault and persisted readback exist.
Do not treat these checks as VB compilation or Inventor/Vault qualification.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = (ROOT / "scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb").read_text(encoding="utf-8-sig")

class PropertyRefreshSafetyGate(unittest.TestCase):
    def test_apply_is_still_blocked(self):
        self.assertRegex(WRAPPER, r'(?is)If apply Then\s*MessageBox\.Show\("APPLY BLOCKED.*?\)\s*Return')

    def test_no_implicit_ga_folder_authority(self):
        self.assertNotRegex(WRAPPER, r'(?i)Dim root As String = System\.IO\.Path\.GetDirectoryName\(active\.FullFileName\)')

    def test_no_lexical_only_containment(self):
        self.assertNotRegex(WRAPPER, r'(?i)If Not full\.StartsWith\(basePath')

    def test_vault_checkout_owner_is_verified_before_mutation(self):
        self.assertRegex(WRAPPER, r'(?i)(?:VaultCheckoutOwnerVerified|VerifyVaultCheckoutOwnership)\s*\(')

    def test_persisted_readback_is_independent(self):
        self.assertRegex(WRAPPER, r'(?i)(?:VerifyPersistedReadback|ReopenAndVerifyProperties)\s*\(')

    def test_no_unqualified_save_in_dormant_apply(self):
        self.assertNotIn("doc.Save2(False)", WRAPPER)

if __name__ == "__main__":
    unittest.main()
