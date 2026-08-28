import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))

from models.audit_event import AuditEvent


class AuditEventTests(unittest.TestCase):
    def test_default_fields(self):
        event = AuditEvent(kind="erasure")
        self.assertEqual(event.kind, "erasure")
        self.assertIsInstance(event.id, str)
        self.assertEqual(len(event.id), 36)  # UUID4 length with dashes
        self.assertIsInstance(event.timestamp, str)

    def test_to_dict_round_trip(self):
        event = AuditEvent(
            kind="recovery",
            drive_path="/dev/sda",
            serial="SN123456",
            method_title="PhotoRec",
            status="succeeded",
            hash_before="abc123",
            files_recovered=42,
        )
        d = event.to_dict()
        self.assertEqual(d["kind"], "recovery")
        self.assertEqual(d["drive_path"], "/dev/sda")
        self.assertEqual(d["files_recovered"], 42)
        restored = AuditEvent.from_dict(d)
        self.assertEqual(restored.kind, event.kind)
        self.assertEqual(restored.drive_path, event.drive_path)
        self.assertEqual(restored.files_recovered, event.files_recovered)

    def test_from_dict_ignores_unknown_keys(self):
        d = {"kind": "file_erase", "unknown_future_field": "value",
             "files_erased": 5, "status": "succeeded"}
        event = AuditEvent.from_dict(d)
        self.assertEqual(event.kind, "file_erase")
        self.assertEqual(event.files_erased, 5)

    def test_log_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["FORENSIDRIVE_LOG_DIR"] = tmpdir
            try:
                import core.audit as audit
                # Force reload with new env
                audit_path = Path(tmpdir) / "audit.jsonl"
                event = AuditEvent(kind="erasure", drive_path="/dev/sdb",
                                   status="succeeded")
                audit.log_event(event)
                self.assertTrue(audit_path.exists())
                events = audit.read_events()
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0].kind, "erasure")
                self.assertEqual(events[0].drive_path, "/dev/sdb")
            finally:
                del os.environ["FORENSIDRIVE_LOG_DIR"]


if __name__ == "__main__":
    unittest.main()
