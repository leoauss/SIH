import os
import sys
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from core.hashing import format_hash, hash_file


class HashingTests(unittest.TestCase):
    def test_hash_file_sha256(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello forensidrive")
            name = f.name
        try:
            digest = hash_file(name, "sha256")
            self.assertEqual(len(digest), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in digest))
        finally:
            os.unlink(name)

    def test_hash_file_md5(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            name = f.name
        try:
            digest = hash_file(name, "md5")
            self.assertEqual(len(digest), 32)
        finally:
            os.unlink(name)

    def test_hash_missing_file_returns_empty(self):
        digest = hash_file("/nonexistent/path/that/does/not/exist.bin")
        self.assertEqual(digest, "")

    def test_format_hash_short(self):
        result = format_hash("abc123")
        self.assertEqual(result, "abc123")

    def test_format_hash_long(self):
        digest = "a" * 64
        result = format_hash(digest)
        self.assertIn("...", result)
        self.assertLess(len(result), 64)

    def test_format_hash_empty(self):
        self.assertEqual(format_hash(""), "unavailable")


if __name__ == "__main__":
    unittest.main()
