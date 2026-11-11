"""Additional fail-closed regression checks for the v2.2.34 offline preview.

These checks exercise the existing read-only gate; passing them would NOT
certify Inventor/Vault evidence or authorise reference mutation.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "repair_preview_gate", Path(__file__).with_name("repair_preview_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class FailClosedPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "OLD.ipt"
        self.src.write_bytes(b"offline fixture")

    def entry(self, path=None):
        return {"path": str(path or self.src), "references_resolved": True,
                "ownership_verified": True, "writable_verified": True}

    def inventory(self, **overrides):
        value = {"target_root": str(self.root), "substitutions": [["OLD", "NEW"]],
                 "files": [self.entry()], "discovery_complete": True,
                 "reverse_references_complete": True,
                 "frame_generator_verified": True,
                 "vault_clearance_verified": True,
                 "profiling_available": True}
        value.update(overrides)
        return value

    def test_unreadable_directory_blocks_even_if_target_does_not_exist(self):
        with patch.object(gate.os, "listdir", side_effect=PermissionError("denied")):
            result = gate.preview(self.inventory())
        self.assertTrue(any(x.startswith("DESTINATION_DIRECTORY_UNREADABLE:")
                            for x in result["preflight_blockers"]))
        self.assertFalse(result["approved_for_mutation"])

    def test_missing_source_blocks(self):
        self.src.unlink()
        result = gate.preview(self.inventory())
        self.assertTrue(any(x.startswith("MISSING_SOURCE:")
                            for x in result["preflight_blockers"]))

    def test_duplicate_source_blocks_case_insensitively(self):
        upper = self.entry()
        lower = self.entry(self.root / "old.IPT")
        result = gate.preview(self.inventory(files=[upper, lower]))
        self.assertTrue(any(x.startswith("DUPLICATE_SOURCE:")
                            for x in result["preflight_blockers"]))

    def test_all_external_certification_flags_are_required(self):
        for flag, prefix in (
            ("discovery_complete", "DISCOVERY_NOT_CERTIFIED"),
            ("reverse_references_complete", "REVERSE_REFERENCES_NOT_CERTIFIED"),
            ("frame_generator_verified", "FRAME_GENERATOR_NOT_VERIFIED"),
            ("vault_clearance_verified", "VAULT_CLEARANCE_NOT_VERIFIED"),
            ("profiling_available", "PROFILING_NOT_AVAILABLE"),
        ):
            with self.subTest(flag=flag):
                result = gate.preview(self.inventory(**{flag: False}))
                self.assertIn(prefix, result["preflight_blockers"])
                self.assertFalse(result["approved_for_mutation"])

    def test_source_ownership_and_writability_flags_required(self):
        for field, prefix in (("ownership_verified", "OWNERSHIP_UNKNOWN:"),
                              ("writable_verified", "WRITABILITY_UNKNOWN:"),
                              ("references_resolved", "UNRESOLVED_REFERENCES:")):
            with self.subTest(field=field):
                entry = self.entry()
                entry[field] = False
                result = gate.preview(self.inventory(files=[entry]))
                self.assertTrue(any(x.startswith(prefix)
                                    for x in result["preflight_blockers"]))


if __name__ == "__main__":
    unittest.main()
