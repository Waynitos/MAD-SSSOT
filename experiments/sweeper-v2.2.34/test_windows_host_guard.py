"""Regression: offline preview must not misinterpret Windows paths on POSIX."""
import os
import unittest
from unittest.mock import patch
import repair_preview_gate as gate

class WindowsHostGuardTests(unittest.TestCase):
    def test_non_windows_host_rejected_before_inventory_path_checks(self):
        with patch.object(gate.os, "name", "posix"):
            with self.assertRaisesRegex(RuntimeError, "WINDOWS_HOST_REQUIRED"):
                gate.preview({"target_root": r"C:\\CAD\\Target", "files": [], "substitutions": []})

    @unittest.skipUnless(os.name == "nt", "Requires a Windows filesystem")
    def test_windows_host_does_not_raise_host_guard(self):
        with self.assertRaisesRegex(ValueError, "target_root"):
            gate.preview({"target_root": "", "files": [], "substitutions": []})

if __name__ == "__main__":
    unittest.main()
