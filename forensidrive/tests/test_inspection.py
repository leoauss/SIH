import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from core.storage import get_drive, list_drives
from models.drive import Drive


class InspectionTests(unittest.TestCase):
    def test_drive_display_and_identity(self):
        with patch.dict(os.environ, {"FORENSIDRIVE_DEMO": "1"}):
            drives = list_drives()
        usb = next(d for d in drives if d.path == "/dev/sda")
        self.assertEqual(usb.display_title(), "Example USB Drive")
        identity = "\n".join(usb.identity_lines())
        self.assertIn("/dev/sda", identity)
        self.assertIn("16.0 GB", identity)
        self.assertIn("unplugged", usb.friendly_kind())

    def test_get_drive(self):
        with patch.dict(os.environ, {"FORENSIDRIVE_DEMO": "1"}):
            drive = get_drive("/dev/nvme0n1")
        self.assertIsInstance(drive, Drive)
        self.assertEqual(drive.partitions[0].path, "/dev/nvme0n1p1")
        self.assertTrue(drive.partitions[0].files_accessible())


if __name__ == "__main__":
    unittest.main()
