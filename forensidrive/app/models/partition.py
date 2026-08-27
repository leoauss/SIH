from dataclasses import dataclass


@dataclass
class Partition:
    name: str
    path: str
    size_bytes: int = 0
    size_label: str = ""
    filesystem: str = ""
    mountpoint: str = ""
    label: str = ""
    read_only: bool = False

    def display_title(self) -> str:
        if self.label:
            return self.label
        return self.name or self.path

    def files_accessible(self) -> bool:
        return bool(self.mountpoint)

    def filesystem_label(self) -> str:
        return self.filesystem or "unknown format"
