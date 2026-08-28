"""Recovery tool adapters. Detection first; GUI never constructs argv."""

from dataclasses import dataclass
from typing import List, Optional

from core.commands import command_exists
from models.drive import Drive


@dataclass
class RecoveryMethod:
    id: str
    title: str
    summary: str
    tool: str
    available: bool
    notes: str = ""

    def missing_message(self) -> str:
        return (
            "This recovery option is not available on this computer because "
            "the '%s' tool was not found." % self.tool
        )


def _photorec() -> RecoveryMethod:
    present = command_exists("photorec")
    return RecoveryMethod(
        id="photorec_common",
        title="Recover common files",
        summary="Look for pictures, documents, and other everyday files.",
        tool="photorec",
        available=present,
        notes="Uses PhotoRec when it is present on SystemRescue.",
    )


def _foremost() -> RecoveryMethod:
    present = command_exists("foremost")
    return RecoveryMethod(
        id="foremost_common",
        title="Recover common files (alternate tool)",
        summary="Another way to look for everyday files if PhotoRec is not available.",
        tool="foremost",
        available=present,
        notes="Uses foremost when it is present.",
    )


def list_methods() -> List[RecoveryMethod]:
    methods = [_photorec(), _foremost()]
    testdisk_present = command_exists("testdisk")
    methods.append(
        RecoveryMethod(
            id="testdisk_not_wired",
            title="Repair drive structure (not offered yet)",
            summary="TestDisk can help with lost partitions, but it is interactive and not wired into this version.",
            tool="testdisk",
            available=False,
            notes="Detected testdisk: %s. Deferred because it is not a safe one-click GUI flow."
            % ("yes" if testdisk_present else "no"),
        )
    )
    return methods


def usable_methods() -> List[RecoveryMethod]:
    return [method for method in list_methods() if method.available]


def get_method(method_id: str) -> RecoveryMethod:
    for method in list_methods():
        if method.id == method_id:
            return method
    raise KeyError(method_id)


def prepare_destination(method_id: str, destination: str) -> str:
    """
    Prepare the output directory for a recovery method.
    Foremost requires the output directory to NOT exist, so we create
    a unique subdirectory. PhotoRec handles existing dirs fine.
    Returns the actual output path to use.
    """
    import os
    from datetime import datetime
    if method_id == "foremost_common":
        # Foremost refuses to run if output dir already exists.
        # Create a unique subdirectory inside the user's chosen folder.
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        actual_dest = os.path.join(destination, "foremost_%s" % ts)
        # Do NOT create it — foremost creates it itself and fails if it exists.
        return actual_dest
    # For PhotoRec, ensure the directory exists
    os.makedirs(destination, exist_ok=True)
    return destination


def build_command(method: RecoveryMethod, drive: Drive, destination: str, partition_path: Optional[str] = None) -> List[str]:
    source = partition_path or drive.path
    if method.id == "photorec_common":
        dest = destination if destination.endswith(("/", "\\")) else destination + "/"
        return [
            "photorec",
            "/d",
            dest,
            "/cmd",
            source,
            "search",
        ]
    if method.id == "foremost_common":
        return ["foremost", "-v", "-t", "all", "-i", source, "-o", destination]
    raise RuntimeError("No command is defined for recovery method %s" % method.id)
