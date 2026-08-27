"""Erasure tool adapters. Detection first; never claim a wipe is 'secure'."""

from dataclasses import dataclass
from typing import List

from core.commands import command_exists
from models.drive import Drive


@dataclass
class EraseMethod:
    id: str
    title: str
    summary: str
    warning: str
    tool: str
    available: bool
    notes: str = ""

    def missing_message(self) -> str:
        return (
            "This erase option is not available on this computer because "
            "the '%s' tool was not found." % self.tool
        )


def list_methods() -> List[EraseMethod]:
    return [
        EraseMethod(
            id="wipefs_signatures",
            title="Remove drive labels",
            summary="Clear the labels that help the computer recognize folders on this drive.",
            warning="Files may still be recoverable afterwards. This does not promise that data is gone forever.",
            tool="wipefs",
            available=command_exists("wipefs"),
            notes="Runs wipefs when the tool is present. Does not overwrite file contents.",
        ),
        EraseMethod(
            id="blkdiscard_discard",
            title="Discard storage (often used on solid-state drives)",
            summary="Ask the drive to throw away stored data using discard.",
            warning="Results depend on the drive. ForensiDrive will not call this a secure erase.",
            tool="blkdiscard",
            available=command_exists("blkdiscard"),
            notes="Runs blkdiscard when the tool is present.",
        ),
        EraseMethod(
            id="shred_overwrite",
            title="Overwrite the drive",
            summary="Write over the drive so old files are much harder to use.",
            warning="This can take a long time. ForensiDrive will not call this a guaranteed secure erase.",
            tool="shred",
            available=command_exists("shred"),
            notes="Runs shred with a single overwrite pass when the tool is present.",
        ),
    ]


def usable_methods() -> List[EraseMethod]:
    return [method for method in list_methods() if method.available]


def get_method(method_id: str) -> EraseMethod:
    for method in list_methods():
        if method.id == method_id:
            return method
    raise KeyError(method_id)


def build_command(method: EraseMethod, drive: Drive) -> List[str]:
    if method.id == "wipefs_signatures":
        return ["wipefs", "--all", "--force", drive.path]
    if method.id == "blkdiscard_discard":
        return ["blkdiscard", drive.path]
    if method.id == "shred_overwrite":
        return ["shred", "-v", "-n", "1", drive.path]
    raise RuntimeError("No command is defined for erase method %s" % method.id)
