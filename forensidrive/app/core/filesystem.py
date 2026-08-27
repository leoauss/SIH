"""Friendly wrappers around mount state."""

from typing import List

from core.errors import AppError
from core.partitions import mounted_partitions
from integrations.filesystem_tools import unmount_path
from models.drive import Drive
from models.partition import Partition


def close_drive(drive: Drive) -> List[str]:
    """Unmount accessible filesystems on a drive. Returns technical notes."""
    notes = []
    still_open = []
    for partition in mounted_partitions(drive.path):
        result = unmount_path(partition.mountpoint or partition.path)
        notes.append(result.technical_text())
        if not result.ok:
            still_open.append(partition.display_title())
    if still_open:
        raise AppError(
            "We couldn't close the drive before continuing. Some files are still in use.",
            "Still accessible: %s\n\n%s" % (", ".join(still_open), "\n\n".join(notes)),
        )
    return notes


def summarize_access(partition: Partition) -> str:
    if partition.files_accessible():
        return "Files currently accessible at %s" % partition.mountpoint
    return "Files are not currently accessible from this area of the drive."
