"""Regression coverage for untrusted frame/profiler evidence; offline only."""
import unittest
from evidence_manifest_validator import validate
from test_evidence_manifest_validator import sample


class ExtendedManifestTests(unittest.TestCase):
    def test_frame_record_must_be_mapping(self):
        manifest = sample()
        manifest["frame_generator"] = ["untrusted"]
        self.assertIn("INVALID_FRAME_RECORD:0", validate(manifest))

    def test_frame_ids_must_resolve(self):
        manifest = sample()
        manifest["frame_generator"] = [{
            "frame_assembly_identity": "ga",
            "skeleton_identity": "missing",
            "member_identity": "missing",
            "external_reference": False,
        }]
        self.assertIn("UNRESOLVED_FRAME_RELATION:0", validate(manifest))

    def test_external_frame_link_blocks(self):
        manifest = sample()
        manifest["frame_generator"] = [{
            "frame_assembly_identity": "ga",
            "skeleton_identity": "ga",
            "member_identity": "ga",
            "external_reference": True,
        }]
        self.assertIn("FRAME_EXTERNAL_REFERENCE_UNVERIFIED:0", validate(manifest))

    def test_missing_profiler_evidence_blocks(self):
        self.assertIn("PROFILER_EVIDENCE_MISSING", validate(sample()))

    def test_profiler_shape_does_not_authorize(self):
        manifest = sample()
        manifest["profiler"] = {"baseline": "v2.2.33", "checkpoints": []}
        blockers = validate(manifest)
        self.assertNotIn("PROFILER_EVIDENCE_MISSING", blockers)
        self.assertIn("EXECUTION_PREFLIGHT_REQUIRED", blockers)


if __name__ == "__main__":
    unittest.main()
