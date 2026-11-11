"""Security regression cases for the offline-only preview gate.
These tests intentionally document currently unresolved safety weaknesses.
No CAD or Vault mutation is performed.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("repair_preview_gate", Path(__file__).with_name("repair_preview_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class SecurityPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "OLD.ipt"
        self.src.write_bytes(b"fixture")

    def data(self, **changes):
        item = {"path": str(self.src), "references_resolved": True,
                "ownership_verified": True, "writable_verified": True}
        value = {"target_root": str(self.root), "files": [item],
                 "substitutions": [["OLD", "NEW"]],
                 "discovery_complete": True, "reverse_references_complete": True,
                 "frame_generator_verified": True, "vault_clearance_verified": True,
                 "profiling_available": True}
        value.update(changes)
        return value

    def test_reserved_windows_device_name_is_blocked(self):
        result = gate.preview(self.data(substitutions=[["OLD", "CON"]]))
        self.assertTrue(any(x.startswith("INVALID_TARGET_NAME:") for x in result["preflight_blockers"]))

    def test_control_character_in_name_is_blocked(self):
        result = gate.preview(self.data(substitutions=[["OLD", "BAD\nNAME"]]))
        self.assertTrue(any(x.startswith("INVALID_TARGET_NAME:") for x in result["preflight_blockers"]))

    def test_symlink_outside_root_is_blocked(self):
        outside = self.root.parent / (self.root.name + "_external.ipt")
        outside.write_bytes(b"external")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        link = self.root / "OLD_LINK.ipt"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this host")
        result = gate.preview(self.data(files=[dict(path=str(link), references_resolved=True,
            ownership_verified=True, writable_verified=True)]))
        self.assertTrue(any("ESCAPE" in x or "OUTSIDE_ROOT" in x for x in result["preflight_blockers"]))

if __name__ == "__main__":
    unittest.main()
