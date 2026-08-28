import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from integrations.file_erase_tools import (
    build_file_command,
    build_folder_command,
    list_file_methods,
)
from models.file_target import FileTarget


class FileEraseToolsTests(unittest.TestCase):
    def test_all_methods_have_warnings(self):
        for m in list_file_methods():
            self.assertGreater(len(m.warning), 0)

    def test_shred_command_targets_path(self):
        with patch("integrations.file_erase_tools.command_exists", return_value=True):
            methods = list_file_methods()
        shred = next(m for m in methods if m.id == "shred_file")
        argv = build_file_command(shred, "/tmp/testfile.txt")
        self.assertIn("/tmp/testfile.txt", argv)
        self.assertNotIn(";", " ".join(argv))

    def test_python_zero_returns_empty_list(self):
        with patch("integrations.file_erase_tools.command_exists", return_value=True):
            methods = list_file_methods()
        python_m = next(m for m in methods if m.id == "python_zero")
        argv = build_file_command(python_m, "/tmp/test.txt")
        self.assertEqual(argv, [])

    def test_file_target_display_name(self):
        t = FileTarget(path="/mnt/data/evidence/photo.jpg", size_bytes=2048,
                       size_label="2 KB", is_dir=False)
        self.assertEqual(t.display_name(), "photo.jpg")
        self.assertEqual(t.kind_label(), "File")

    def test_folder_target(self):
        t = FileTarget(path="/mnt/data/case_files", size_bytes=10240,
                       size_label="10 KB", is_dir=True)
        self.assertEqual(t.kind_label(), "Folder")


if __name__ == "__main__":
    unittest.main()
