"""Physical storage discovery using structured lsblk output."""

import json
import os
from typing import List

from core.commands import command_exists, run_command
from core.errors import AppError, DeviceGoneError
from models.drive import Drive
from models.partition import Partition

LSBLK_COLUMNS = [
    "NAME",
    "PATH",
    "KNAME",
    "MODEL",
    "VENDOR",
    "SIZE",
    "TYPE",
    "RM",
    "RO",
    "ROTA",
    "FSTYPE",
    "MOUNTPOINT",
    "LABEL",
    "SERIAL",
    "TRAN",
    "HOTPLUG",
]

SKIP_TYPES = {"loop", "ram", "rom"}


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if value in (1, "1", "true", "True"):
        return True
    return False


def _as_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def format_size(num_bytes: int) -> str:
    if num_bytes <= 0:
        return "unknown size"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return "%d B" % int(size)
            return "%.1f %s" % (size, unit)
        size /= 1024.0
    return "%s B" % num_bytes


def _node_path(node: dict) -> str:
    path = node.get("path") or ""
    if path:
        return path
    name = node.get("name") or node.get("kname") or ""
    if name.startswith("/dev/"):
        return name
    if name:
        return "/dev/" + name
    return ""


def _partition_from_node(node: dict) -> Partition:
    size_bytes = _as_int(node.get("size"))
    return Partition(
        name=node.get("name") or node.get("kname") or "",
        path=_node_path(node),
        size_bytes=size_bytes,
        size_label=format_size(size_bytes),
        filesystem=node.get("fstype") or "",
        mountpoint=node.get("mountpoint") or "",
        label=node.get("label") or "",
        read_only=_truthy(node.get("ro")),
    )


def _drive_from_node(node: dict) -> Drive:
    size_bytes = _as_int(node.get("size"))
    children = node.get("children") or []
    partitions = []
    for child in children:
        child_type = (child.get("type") or "").lower()
        if child_type in SKIP_TYPES:
            continue
        if child_type in ("part", "crypt", "lvm", "md"):
            partitions.append(_partition_from_node(child))
        elif child.get("children"):
            partitions.append(_partition_from_node(child))
    model = (node.get("model") or "").strip()
    if not model and (node.get("type") or "").lower() == "loop":
        model = "Virtual Disk (Loop)"
    return Drive(
        name=node.get("name") or node.get("kname") or "",
        path=_node_path(node),
        model=model,
        vendor=(node.get("vendor") or "").strip(),
        size_bytes=size_bytes,
        size_label=format_size(size_bytes),
        removable=_truthy(node.get("rm")) or _truthy(node.get("hotplug")),
        read_only=_truthy(node.get("ro")),
        transport=(node.get("tran") or "").strip(),
        serial=(node.get("serial") or "").strip(),
        rota=_truthy(node.get("rota", True)),  # default True (HDD) if absent
        partitions=partitions,
    )


def demo_drives() -> List[Drive]:
    """Synthetic drives for UI testing. Enabled with FORENSIDRIVE_DEMO=1."""
    return [
        Drive(
            name="sda",
            path="/dev/sda",
            model="Example USB Drive",
            vendor="Demo",
            size_bytes=16 * 1024 ** 3,
            size_label="16.0 GB",
            removable=True,
            transport="usb",
            serial="DEMOUSB001",
            partitions=[
                Partition(
                    name="sda1",
                    path="/dev/sda1",
                    size_bytes=16 * 1024 ** 3,
                    size_label="16.0 GB",
                    filesystem="vfat",
                    mountpoint="",
                    label="USBDATA",
                )
            ],
        ),
        Drive(
            name="nvme0n1",
            path="/dev/nvme0n1",
            model="Example Internal SSD",
            vendor="Demo",
            size_bytes=476 * 1024 ** 3,
            size_label="476.0 GB",
            removable=False,
            transport="nvme",
            serial="DEMOSSD001",
            partitions=[
                Partition(
                    name="nvme0n1p1",
                    path="/dev/nvme0n1p1",
                    size_bytes=512 * 1024 ** 2,
                    size_label="512.0 MB",
                    filesystem="vfat",
                    mountpoint="/boot",
                    label="EFI",
                ),
                Partition(
                    name="nvme0n1p2",
                    path="/dev/nvme0n1p2",
                    size_bytes=475 * 1024 ** 3,
                    size_label="475.0 GB",
                    filesystem="ext4",
                    mountpoint="/",
                    label="root",
                ),
            ],
        ),
    ]


def list_drives() -> List[Drive]:
    if os.environ.get("FORENSIDRIVE_DEMO") == "1":
        return demo_drives()

    if not command_exists("lsblk"):
        raise AppError(
            "We couldn't look up storage drives on this computer.",
            "lsblk is not available. ForensiDrive expects a SystemRescue Linux environment.",
        )

    columns = ",".join(LSBLK_COLUMNS)
    result = run_command(
        ["lsblk", "-J", "-b", "-o", columns],
        timeout=20,
        check=False,
        user_error="We couldn't inspect the storage drives.",
    )
    if result.missing:
        raise AppError(
            "We couldn't look up storage drives on this computer.",
            result.technical_text(),
        )
    if not result.ok:
        raise AppError(
            "We couldn't inspect the storage drives.",
            result.technical_text(),
        )

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise AppError(
            "We couldn't inspect the storage drives.",
            "lsblk JSON could not be read: %s\n\n%s" % (exc, result.stdout),
        )

    drives = []
    for node in payload.get("blockdevices") or []:
        node_type = (node.get("type") or "").lower()
        size_bytes = _as_int(node.get("size"))
        if node_type in SKIP_TYPES:
            continue
        # Include real disks and active loop devices with non-zero size
        if node_type != "disk" and not (node_type == "loop" and size_bytes > 0):
            continue
        drives.append(_drive_from_node(node))
    return drives


def get_drive(path: str) -> Drive:
    for drive in list_drives():
        if drive.path == path:
            return drive
    raise DeviceGoneError(
        "That drive is no longer available. It may have been unplugged.",
        "Requested path: %s" % path,
    )
