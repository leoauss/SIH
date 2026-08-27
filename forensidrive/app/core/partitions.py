"""Partition helpers built on discovered drive data."""

from typing import List

from core.errors import DeviceGoneError
from core.storage import get_drive, list_drives
from models.partition import Partition


def list_partitions(drive_path: str) -> List[Partition]:
    drive = get_drive(drive_path)
    return list(drive.partitions)


def find_partition(path: str) -> Partition:
    for drive in list_drives():
        found = drive.partition_by_path(path)
        if found is not None:
            return found
    raise DeviceGoneError(
        "That part of the drive is no longer available.",
        "Requested path: %s" % path,
    )


def mounted_partitions(drive_path: str) -> List[Partition]:
    return [part for part in list_partitions(drive_path) if part.files_accessible()]
