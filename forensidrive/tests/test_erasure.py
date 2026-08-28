import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from integrations.erasure_tools import build_command, get_method, list_methods
from models.drive import Drive


class ErasureTests(unittest.TestCase):
    def test_missing_tools_are_not_offered_as_available(self):
        with patch("integrations.erasure_tools.command_exists", return_value=False):
            methods = list_methods()
        # python_zero-style fallbacks are always available; tool-based methods should be unavailable
        tool_methods = [m for m in methods if m.tool != "python"]
        self.assertTrue(all(not m.available for m in tool_methods))

    def test_commands_are_lists_and_target_the_selected_drive(self):
        drive = Drive(name="sdd", path="/dev/sdd", model="Disposable", size_label="8.0 GB")
        with patch("integrations.erasure_tools.command_exists", return_value=True):
            for method in list_methods():
                argv = build_command(method, drive)
                self.assertIsInstance(argv, list)
                self.assertNotIn(";", " ".join(argv))
                self.assertIn(drive.path, argv)

    def test_warnings_do_not_claim_secure_erase(self):
        """No method warning should claim to guarantee erasure."""
        with patch("integrations.erasure_tools.command_exists", return_value=True):
            for method in list_methods():
                blob = (method.title + method.summary + method.warning).lower()
                self.assertNotIn("secure erase guaranteed", blob)
                self.assertNotIn("100% unrecoverable", blob)
                self.assertIsInstance(method.warning, str)
                self.assertGreater(len(method.warning), 0)

    def test_compliance_labels_reference_known_standards(self):
        """Methods with named standards should expose a compliance label."""
        with patch("integrations.erasure_tools.command_exists", return_value=True):
            named = [m for m in list_methods()
                     if m.standard_id not in ("", "wipefs_labels", "blkdiscard", "single_random")]
            for method in named:
                label = method.compliance_label
                known = ("NIST", "DoD", "Gutmann", "ATA")
                self.assertTrue(
                    any(k in label for k in known),
                    "Unexpected compliance label %r for method %r" % (label, method.id),
                )

    def test_recommended_method_matches_drive_type(self):
        """SSD drives get blkdiscard; HDDs get dod_3pass."""
        ssd = Drive(name="nvme0n1", path="/dev/nvme0n1", model="FastSSD",
                    size_label="512 GB", rota=False)
        hdd = Drive(name="sda", path="/dev/sda", model="OldHDD",
                    size_label="1.0 TB", rota=True)
        self.assertEqual(ssd.recommended_erase_standard(), "blkdiscard_discard")
        self.assertEqual(hdd.recommended_erase_standard(), "dod_3pass")


if __name__ == "__main__":
    unittest.main()
