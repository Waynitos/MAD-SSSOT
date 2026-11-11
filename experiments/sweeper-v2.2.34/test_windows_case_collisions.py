"""Offline regression cases for Windows case-insensitive destination occupancy.
These tests are deliberately fail-closed specifications, not Inventor validation.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "repair_preview_gate", Path(__file__).with_name("repair_preview_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class WindowsCaseCollisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "OLD.ipt"
        self.source.write_bytes(b"source")

    def inventory(self, files=None):
        return {
            "target_root": str(self.root),
            "substitutions": [["OLD", "NEW"]],
            "files": files if files is not None else [{
                "path": str(self.source), "references_resolved": True,
                "ownership_verified": True, "writable_verified": True}],
            "discovery_complete": True,
            "reverse_references_complete": True,
            "frame_generator_verified": True,
            "vault_clearance_verified": True,
            "profiling_available": True,
        }

    def test_case_variant_occupied_destination_is_blocked(self):
        occupied = self.root / "new.IPT"
        occupied.write_bytes(b"occupied")
        result = gate.preview(self.inventory())
        self.assertFalse(result["approved_for_mutation"])
        self.assertTrue(any(x.startswith("DESTINATION_EXISTS:") or
                            x.startswith("DESTINATION_CASE_COLLISION:")
                            for x in result["preflight_blockers"]))

    def test_case_variant_unlisted_source_is_blocked(self):
        occupied = self.root / "new.ipt"
        occupied.write_bytes(b"unlisted Inventor file")
        result = gate.preview(self.inventory())
        self.assertTrue(result["preflight_blockers"])

    def test_case_variant_destination_within_inventory_is_blocked(self):
        occupied = self.root / "new.IPT"
        occupied.write_bytes(b"second source")
        files = [
            {"path": str(path), "references_resolved": True,
             "ownership_verified": True, "writable_verified": True}
            for path in (self.source, occupied)]
        result = gate.preview(self.inventory(files=files))
        self.assertTrue(any(x.startswith("DESTINATION_COLLISION:") or
                            x.startswith("DESTINATION_IS_SOURCE:")
                            for x in result["preflight_blockers"]))


if __name__ == "__main__":
    unittest.main()
