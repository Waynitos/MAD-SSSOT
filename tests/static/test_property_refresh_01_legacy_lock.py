"""Static regression guard for the retired direct property-refresh entry point.

This is a source-level safety check, NOT Inventor/Vault validation.
Run: python -m unittest tests/static/test_property_refresh_01_legacy_lock.py
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_DIRECT_TEST_01.iLogicVb"

class LegacyDirectRuleLock(unittest.TestCase):
    def test_entry_point_has_unconditional_return_before_any_legacy_logic(self):
        source = LEGACY.read_text(encoding="utf-8-sig")
        main = re.search(r"(?im)^\s*Sub\s+Main\s*\(\s*\)", source)
        self.assertIsNotNone(main, "Missing legacy Main entry point")
        body = source[main.end():]
        statements = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("'"):
                continue
            statements.append(stripped)
            if len(statements) == 2:
                break
        self.assertEqual(len(statements), 2, "Expected safety notice followed by unconditional Return")
        self.assertRegex(statements[0], r'(?i)^MessageBox\.Show\("LEGACY RULE DISABLED:')
        self.assertEqual(statements[1].lower(), "return")

    def test_no_alternative_entry_point(self):
        source = LEGACY.read_text(encoding="utf-8-sig")
        self.assertEqual(len(re.findall(r"(?im)^\s*Sub\s+Main\s*\(", source)), 1)

if __name__ == "__main__":
    unittest.main()
