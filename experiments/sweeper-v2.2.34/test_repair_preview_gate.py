"""Offline regression checks for the preview-only v2.2.34 experiment.

Run on Windows: python -m unittest discover -s experiments/sweeper-v2.2.34 -p 'test_*.py'
No Inventor or Vault execution is performed.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("repair_preview_gate", Path(__file__).with_name("repair_preview_gate.py"))
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class PreviewGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "OLD.ipt"
        self.src.write_bytes(b"fixture")
        self.flags = dict(discovery_complete=True, reverse_references_complete=True,
                          frame_generator_verified=True, vault_clearance_verified=True,
                          profiling_available=True)

    def inventory(self, files=None, substitutions=None, **flags):
        return dict(target_root=str(self.root), substitutions=substitutions if substitutions is not None else [["OLD", "NEW"]],
                    files=files if files is not None else [dict(path=str(self.src), references_resolved=True,
                                                                  ownership_verified=True, writable_verified=True)],
                    **(self.flags | flags))

    def test_preview_never_approves_mutation(self):
        result = gate.preview(self.inventory())
        self.assertFalse(result["approved_for_mutation"])
        self.assertTrue(result["preview_only"])
        self.assertEqual(result["preflight_blockers"], ["EVIDENCE_MANIFEST_MISSING"])
        self.assertEqual(result["plan"][0]["destination"], str(self.root / "NEW.ipt"))
        self.assertTrue(self.src.exists())
        self.assertFalse((self.root / "NEW.ipt").exists())

    def test_untrusted_manifest_is_structurally_checked_and_never_approves(self):
        inventory = self.inventory(evidence_manifest={"schema": "invalid", "documents": []})
        result = gate.preview(inventory)
        self.assertIn("UNSUPPORTED_SCHEMA", result["preflight_blockers"])
        self.assertIn("INVENTOR_READBACK_REQUIRED", result["preflight_blockers"])
        self.assertIn("EXECUTION_PREFLIGHT_REQUIRED", result["preflight_blockers"])
        self.assertNotIn("EVIDENCE_MANIFEST_MISSING", result["preflight_blockers"])
        self.assertFalse(result["approved_for_mutation"])

    def test_uncertified_discovery_blocks(self):
        result = gate.preview(self.inventory(discovery_complete=False))
        self.assertIn("DISCOVERY_NOT_CERTIFIED", result["preflight_blockers"])

    def test_unresolved_references_block(self):
        files = [dict(path=str(self.src), references_resolved=False, ownership_verified=True, writable_verified=True)]
        self.assertTrue(any(x.startswith("UNRESOLVED_REFERENCES:") for x in gate.preview(self.inventory(files=files))["preflight_blockers"]))

    def test_destination_already_exists_blocks(self):
        (self.root / "NEW.ipt").write_bytes(b"occupied")
        self.assertTrue(any(x.startswith("DESTINATION_EXISTS:") for x in gate.preview(self.inventory())["preflight_blockers"]))

    def test_duplicate_destinations_block(self):
        other = self.root / "NEW.ipt"
        other.write_bytes(b"fixture")
        files = [dict(path=str(p), references_resolved=True, ownership_verified=True, writable_verified=True)
                 for p in (self.src, other)]
        self.assertTrue(any(x.startswith("DESTINATION_COLLISION:") for x in gate.preview(self.inventory(files=files))["preflight_blockers"]))

    def test_invalid_target_name_blocks(self):
        self.assertTrue(any(x.startswith("INVALID_TARGET_NAME:") for x in gate.preview(self.inventory(substitutions=[["OLD", "BAD?"]]))["preflight_blockers"]))

    def test_empty_inventory_blocks(self):
        self.assertIn("EMPTY_INVENTORY", gate.preview(self.inventory(files=[]))["preflight_blockers"])

    def test_more_than_five_substitutions_rejected(self):
        with self.assertRaises(ValueError):
            gate.preview(self.inventory(substitutions=[["x", "y"]] * 6))


if __name__ == "__main__":
    unittest.main()
