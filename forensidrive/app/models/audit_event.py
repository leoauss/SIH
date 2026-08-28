"""Typed record for one audit log entry."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class AuditEvent:
    """One structured record written to the audit log per operation."""

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Operation metadata
    kind: str = ""          # "erasure" | "recovery" | "file_erase"
    operator: str = ""      # future: username or session ID

    # Target device / path
    drive_path: str = ""
    serial: str = ""

    # Method used
    method_id: str = ""
    method_title: str = ""
    standard_id: str = ""   # e.g. "nist_clear", "dod_3pass"

    # Result
    status: str = ""        # "succeeded" | "failed" | "cancelled"
    user_message: str = ""

    # Integrity hashes
    hash_before: str = ""   # SHA-256 of source before operation
    hash_after: str = ""    # SHA-256 of source after erasure (verify pass)

    # Recovery-specific
    destination: str = ""   # output folder for recovery
    files_recovered: int = 0

    # File eraser-specific
    files_erased: int = 0
    files_failed: int = 0

    # Raw technical output
    notes: str = ""
    technical_lines: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to a plain dict suitable for JSON encoding."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "kind": self.kind,
            "operator": self.operator,
            "drive_path": self.drive_path,
            "serial": self.serial,
            "method_id": self.method_id,
            "method_title": self.method_title,
            "standard_id": self.standard_id,
            "status": self.status,
            "user_message": self.user_message,
            "hash_before": self.hash_before,
            "hash_after": self.hash_after,
            "destination": self.destination,
            "files_recovered": self.files_recovered,
            "files_erased": self.files_erased,
            "files_failed": self.files_failed,
            "notes": self.notes,
            "technical_lines": self.technical_lines,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEvent":
        """Reconstruct from a stored dict. Unknown keys are silently ignored."""
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
