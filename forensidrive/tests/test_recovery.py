import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from core.classifier import classify_directory, classify_file
from core.evidence import create_case_id, hash_destination_tree, write_chain_of_custody
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
        self.assertEqual(argv, ["foremost", "-v", "-t", "all", "-i", "/dev/sdc", "-o", "/tmp/out"])

    def test_classifier_png(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # PNG signature
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
            name = f.name
        try:
            res = classify_file(name)
            self.assertEqual(res.detected_type, "image/png")
            self.assertEqual(res.category, "images")
            self.assertEqual(res.confidence, "HIGH")
        finally:
            os.unlink(name)

    def test_classifier_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 header bytes")
            name = f.name
        try:
            res = classify_file(name)
            self.assertEqual(res.detected_type, "application/pdf")
            self.assertEqual(res.category, "documents")
            self.assertEqual(res.confidence, "HIGH")
        finally:
            os.unlink(name)

    def test_chain_of_custody_writer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "recovered.jpg"
            file1.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
            dest_hashes = hash_destination_tree(tmpdir)
            self.assertIn("recovered.jpg", dest_hashes)

            case_id = create_case_id()
            coc = write_chain_of_custody(case_id, "/dev/sda", "sourcehash123", dest_hashes, tmpdir, "PhotoRec")
            self.assertTrue(coc.exists())


if __name__ == "__main__":
    unittest.main()
