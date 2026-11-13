"""Offline contract tests for property-refresh planning, not Inventor runtime tests.

Run: python -m unittest tests/static/test_property_refresh_01_drawing_guard.py
These fixtures describe REQUIRED behaviour; they do not claim current rule passes.
"""
import re
import unittest

PROJECT = re.compile(r"^PJ[0-9]{5}(?=-)", re.I)
PREFIX = re.compile(r"^PJ[0-9]{5}$", re.I)

def proposed_drawing_number(filename_stem, existing_value, target):
    if not PREFIX.fullmatch(target):
        raise ValueError("Invalid project prefix")
    if not PROJECT.match(filename_stem):
        return None  # Filename has no leading project prefix: do not overwrite.
    if not PROJECT.match(existing_value or ""):
        return None  # Existing custom property is not a project-coded value.
    if PROJECT.match(filename_stem).group().upper() != PROJECT.match(existing_value).group().upper():
        return None  # Inconsistent project identity: manual review.
    proposed = PROJECT.sub(target.upper(), existing_value, count=1)
    return proposed if proposed != existing_value else None

class DrawingPropertyGuardTests(unittest.TestCase):
    def test_matching_project_prefix_preserves_property_suffix(self):
        self.assertEqual(proposed_drawing_number("PJ00201-3410-01", "PJ00201-DRG-3410-01", "PJ00333"), "PJ00333-DRG-3410-01")
    def test_nonproject_filename_never_overwrites(self):
        self.assertIsNone(proposed_drawing_number("GENERAL-ARRANGEMENT", "PJ00201-DRG-01", "PJ00333"))
    def test_nonproject_existing_value_never_overwrites(self):
        self.assertIsNone(proposed_drawing_number("PJ00201-3410-01", "CUSTOM-NUMBER", "PJ00333"))
    def test_mismatched_project_prefix_requires_review(self):
        self.assertIsNone(proposed_drawing_number("PJ00201-3410-01", "PJ00444-DRG-01", "PJ00333"))
    def test_invalid_prefix_rejected(self):
        with self.assertRaises(ValueError):
            proposed_drawing_number("PJ00201-3410-01", "PJ00201-DRG-01", "PJ33")
    def test_idempotent(self):
        self.assertIsNone(proposed_drawing_number("PJ00333-3410-01", "PJ00333-DRG-01", "PJ00333"))
    def test_suffix_internal_prefix_unchanged(self):
        self.assertEqual(proposed_drawing_number("PJ00201-3410-01", "PJ00201-DRG-PJ00201", "PJ00333"), "PJ00333-DRG-PJ00201")

if __name__ == "__main__":
    unittest.main()
