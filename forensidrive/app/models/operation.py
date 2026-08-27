from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


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

    def add_technical(self, line: str) -> None:
        self.technical_lines.append(line)
