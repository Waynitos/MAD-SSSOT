"""PROPERTY REFRESH TEST 01: static contract guard (not Inventor runtime validation)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "scripts" / "ilogic" / "experiments"

class DiscoveryReadbackGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery = (BASE / "BEEXCITED_PropertyRefreshDiscovery.iLogicVb").read_text(encoding="utf-8")
        cls.readback = (BASE / "BEEXCITED_PropertyRefreshReadback.iLogicVb").read_text(encoding="utf-8")
        cls.wrapper = (BASE / "BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb").read_text(encoding="utf-8")

    def test_assembly_root_and_recursive_refs(self):
        self.assertIn("AddModelPath(active.FullFileName", self.discovery)
        self.assertIn("active.AllReferencedDocuments", self.discovery)
        self.assertIn('extension <> ".iam" AndAlso extension <> ".ipt"', self.discovery)

    def test_drawing_folder_includes_active_and_both_extensions(self):
        self.assertIn("result.Add(full)", self.discovery)
        self.assertIn("Directory.GetFiles(folder", self.discovery)
        self.assertIn('candidateExtension <> ".idw" AndAlso candidateExtension <> ".dwg"', self.discovery)

    def test_shared_readback_is_not_persisted_verification(self):
        self.assertIn("doc.PropertySets.Item(setName).Item(propertyName).Value", self.readback)
        self.assertIn("This checks memory only", self.readback)
        self.assertNotIn(".Save2(", self.readback)
        self.assertNotIn(".SaveAs(", self.readback)

    def test_wrapper_calls_shared_discovery_and_blocks_apply(self):
        self.assertIn("BEEXCITED_PropertyRefreshDiscovery.DiscoverAssemblyModels", self.wrapper)
        self.assertIn("BEEXCITED_PropertyRefreshDiscovery.DiscoverDrawingFolder", self.wrapper)
        self.assertIn("APPLY BLOCKED", self.wrapper)
        self.assertNotIn(".Save2(", self.wrapper)

if __name__ == "__main__":
    unittest.main()
