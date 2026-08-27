import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from core.commands import CommandResult
from core.errors import AppError
from core.storage import format_size, list_drives


SAMPLE = {
    "blockdevices": [
        {
            "name": "sda",
            "path": "/dev/sda",
            "kname": "sda",
            "model": "Samsung SSD",
            "vendor": "Samsung",
            "size": 512110190592,
            "type": "disk",
            "rm": False,
            "ro": False,
            "fstype": None,
            "mountpoint": None,
            "label": None,
            "serial": "S123",
            "tran": "sata",
            "hotplug": False,
            "children": [
                {
                    "name": "sda1",
                    "path": "/dev/sda1",
                    "size": 512110190592,
                    "type": "part",
                    "rm": False,
                    "ro": False,
                    "fstype": "ext4",
                    "mountpoint": "/",
                    "label": "root",
                }
            ],
        },
        {
            "name": "loop0",
            "path": "/dev/loop0",
            "size": 1000,
            "type": "loop",
            "rm": False,
            "ro": False,
        },
    ]
}


class StorageTests(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(format_size(0), "unknown size")
        self.assertIn("GB", format_size(16 * 1024 ** 3))

    def test_demo_drives(self):
        with patch.dict(os.environ, {"FORENSIDRIVE_DEMO": "1"}):
            drives = list_drives()
        self.assertGreaterEqual(len(drives), 1)
        self.assertTrue(all(d.path.startswith("/dev/") for d in drives))

    def test_lsblk_json(self):
        result = CommandResult(
            argv=["lsblk"],
            returncode=0,
            stdout=json.dumps(SAMPLE),
            stderr="",
        )
        with patch.dict(os.environ, {"FORENSIDRIVE_DEMO": "0"}, clear=False):
            os.environ.pop("FORENSIDRIVE_DEMO", None)
            with patch("core.storage.command_exists", return_value=True):
                with patch("core.storage.run_command", return_value=result):
                    drives = list_drives()
        self.assertEqual(len(drives), 1)
        self.assertEqual(drives[0].path, "/dev/sda")
        self.assertEqual(drives[0].model, "Samsung SSD")
        self.assertEqual(len(drives[0].partitions), 1)
        self.assertEqual(drives[0].partitions[0].filesystem, "ext4")

    def test_missing_lsblk(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FORENSIDRIVE_DEMO", None)
            with patch("core.storage.command_exists", return_value=False):
                with self.assertRaises(AppError) as ctx:
                    list_drives()
        self.assertIn("couldn't look up storage drives", ctx.exception.user_message.lower())


if __name__ == "__main__":
    unittest.main()
