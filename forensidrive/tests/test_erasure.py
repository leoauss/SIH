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
        self.assertTrue(all(not method.available for method in methods))

    def test_commands_are_lists_and_target_the_selected_drive(self):
        drive = Drive(name="sdd", path="/dev/sdd", model="Disposable", size_label="8.0 GB")
        with patch("integrations.erasure_tools.command_exists", return_value=True):
            for method in list_methods():
                argv = build_command(method, drive)
                self.assertIsInstance(argv, list)
                self.assertNotIn(";", " ".join(argv))
                self.assertIn(drive.path, argv)

    def test_warnings_do_not_claim_secure_erase(self):
        with patch("integrations.erasure_tools.command_exists", return_value=True):
            for method in list_methods():
                blob = (method.title + method.summary + method.warning).lower()
                self.assertNotIn("secure erase guaranteed", blob)
                self.assertIn("not", method.warning.lower())


if __name__ == "__main__":
    unittest.main()
