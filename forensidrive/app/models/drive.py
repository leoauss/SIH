from dataclasses import dataclass, field
from typing import List, Optional

from models.partition import Partition


@dataclass
class Drive:
    """A physical storage drive, described in both simple and technical terms."""

    name: str
    path: str
    model: str = ""
    vendor: str = ""
    size_bytes: int = 0
    size_label: str = ""
    removable: bool = False
    read_only: bool = False
    transport: str = ""
    serial: str = ""
    partitions: List[Partition] = field(default_factory=list)

    def display_title(self) -> str:
        title = self.model or self.vendor or self.name
        return title.strip() or self.path

    def identity_lines(self) -> List[str]:
        lines = [
            f"Name: {self.display_title()}",
            f"Drive path: {self.path}",
            f"Size: {self.size_label or 'unknown'}",
        ]
        if self.serial:
            lines.append(f"Serial: {self.serial}")
        if self.vendor:
            lines.append(f"Vendor: {self.vendor}")
        return lines

    def friendly_kind(self) -> str:
        if self.transport.lower() == "usb" or self.removable:
            return "This looks like a drive that can be unplugged."
        return "This looks like a drive inside the computer."

    def partition_by_path(self, path: str) -> Optional[Partition]:
        for partition in self.partitions:
            if partition.path == path:
                return partition
        return None
