"""A file or folder selected as a target for secure deletion."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileTarget:
    """Represents one file or folder queued for secure erasure."""

    path: str
    size_bytes: int = 0
    size_label: str = ""
    is_dir: bool = False
    filesystem: str = ""
    selected: bool = True

    def display_name(self) -> str:
        """Short name for display in lists."""
        return Path(self.path).name or self.path

    def display_path(self) -> str:
        """Full path, truncated from the left if very long."""
        if len(self.path) <= 60:
            return self.path
        return "..." + self.path[-57:]

    def kind_label(self) -> str:
        return "Folder" if self.is_dir else "File"
