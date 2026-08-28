from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid


class OperationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Operation:
    kind: str
    title: str
    status: OperationStatus = OperationStatus.IDLE
    user_message: str = ""
    technical_lines: List[str] = field(default_factory=list)
    return_code: Optional[int] = None
    command: List[str] = field(default_factory=list)
    # Audit and integrity fields (Phase 1)
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_path: str = ""           # drive/file path being operated on
    destination: str = ""           # output folder (recovery/file erase)
    hash_before: Optional[str] = None  # SHA-256 of source before operation
    hash_after: Optional[str] = None   # SHA-256 of source after operation
    standard_id: str = ""          # erasure standard applied

    def add_technical(self, line: str) -> None:
        self.technical_lines.append(line)
