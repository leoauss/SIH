import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from integrations.recovery_tools import build_command, get_method, list_methods
from models.drive import Drive


class RecoveryTests(unittest.TestCase):
    def test_methods_are_detection_based(self):
        with patch("integrations.recovery_tools.command_exists", return_value=False):
            methods = list_methods()
        self.assertTrue(all(not m.available for m in methods if m.id != "testdisk_not_wired"))
        testdisk = next(m for m in methods if m.id == "testdisk_not_wired")
        self.assertFalse(testdisk.available)

    def test_photorec_command_uses_list_argv(self):
        with patch("integrations.recovery_tools.command_exists", return_value=True):
            method = get_method("photorec_common")
        drive = Drive(name="sdb", path="/dev/sdb", model="Stick")
        argv = build_command(method, drive, "/mnt/safe")
        self.assertIsInstance(argv, list)
        self.assertEqual(argv[0], "photorec")
        self.assertIn("/dev/sdb", argv)
        self.assertTrue(any(part.startswith("/mnt/safe") for part in argv))

    def test_foremost_command(self):
        with patch("integrations.recovery_tools.command_exists", return_value=True):
            method = get_method("foremost_common")
        drive = Drive(name="sdc", path="/dev/sdc")
        argv = build_command(method, drive, "/tmp/out")
        self.assertEqual(argv, ["foremost", "-i", "/dev/sdc", "-o", "/tmp/out"])


if __name__ == "__main__":
    unittest.main()
