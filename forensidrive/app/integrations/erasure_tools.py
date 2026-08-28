"""Erasure tool adapters. Supports named compliance standards. Never claims a wipe is 'secure'."""

from dataclasses import dataclass
from typing import List, Optional

from core.commands import command_exists
from core.standards import STANDARDS, ErasureStandard
from models.drive import Drive


@dataclass
class EraseMethod:
    id: str
    title: str
    summary: str
    warning: str
    tool: str
    available: bool
    standard_id: str = ""
    notes: str = ""
    recommended_for_ssd: bool = False
    recommended_for_hdd: bool = False

    @property
    def standard(self) -> Optional[ErasureStandard]:
        return STANDARDS.get(self.standard_id)

    @property
    def compliance_label(self) -> str:
        """Short compliance badge text, e.g. 'NIST 800-88'."""
        s = self.standard
        if not s or s.reference == "None":
            return ""
        # Return first segment before comma
        return s.reference.split(",")[0]

    def missing_message(self) -> str:
        return (
            "This erase option is not available on this computer because "
            "the '%s' tool was not found." % self.tool
        )


def list_methods() -> List[EraseMethod]:
    """Return all erase methods, available or not, in display order."""
    shred_ok = command_exists("shred")
    blkdiscard_ok = command_exists("blkdiscard")
    wipefs_ok = command_exists("wipefs")
    hdparm_ok = command_exists("hdparm")

    return [
        # --- SSD / NVMe methods ---
        EraseMethod(
            id="blkdiscard_discard",
            title="Discard blocks (SSD/NVMe TRIM)",
            summary="Ask the drive to mark all blocks as unused. Fastest option for solid-state drives.",
            warning="Effectiveness depends on the drive firmware. ForensiDrive will not call this a guaranteed erase.",
            tool="blkdiscard",
            available=blkdiscard_ok,
            standard_id="blkdiscard",
            notes="Runs: blkdiscard <device>",
            recommended_for_ssd=True,
        ),
        # --- HDD / General overwrite methods ---
        EraseMethod(
            id="nist_clear",
            title="NIST 800-88 Clear (1-pass zeros)",
            summary="Overwrite the entire drive with zeros once, then verify. Suitable for drives staying within your organisation.",
            warning="Does not meet Purge requirements. Not suitable for SSDs with wear-levelling.",
            tool="shred",
            available=shred_ok,
            standard_id="nist_clear",
            notes="Runs: shred -v -n 0 -z <device> (zero pass + verify)",
            recommended_for_hdd=True,
        ),
        EraseMethod(
            id="dod_3pass",
            title="DoD 5220.22-M — 3-pass overwrite",
            summary="Three passes: zeros, ones, random data. Followed by a verification read. Widely accepted for HDD sanitisation.",
            warning="Can take several hours on large drives. ForensiDrive will not guarantee data is unrecoverable.",
            tool="shred",
            available=shred_ok,
            standard_id="dod_3pass",
            notes="Runs: shred -v -n 3 -z <device>",
            recommended_for_hdd=True,
        ),
        EraseMethod(
            id="dod_7pass",
            title="DoD 5220.22-M ECE — 7-pass overwrite",
            summary="Seven overwrite passes. Rarely required by current guidance; included for completeness.",
            warning="Very slow. Not recommended unless specifically required by your policy.",
            tool="shred",
            available=shred_ok,
            standard_id="dod_7pass",
            notes="Runs: shred -v -n 7 -z <device>",
        ),
        EraseMethod(
            id="gutmann_35pass",
            title="Gutmann — 35-pass overwrite",
            summary="35 overwrite passes. Designed for older encoding schemes. Modern drives do not require this.",
            warning="Extremely slow. Rarely necessary for drives manufactured after 2001.",
            tool="shred",
            available=shred_ok,
            standard_id="gutmann",
            notes="Runs: shred -v -n 35 <device>",
        ),
        # --- Quick label removal ---
        EraseMethod(
            id="wipefs_signatures",
            title="Remove drive labels only",
            summary="Clear the filesystem signatures so the drive appears blank to most tools. File contents are NOT overwritten.",
            warning="Data remains fully recoverable with carving tools. This is NOT an erase method.",
            tool="wipefs",
            available=wipefs_ok,
            standard_id="wipefs_labels",
            notes="Runs: wipefs --all --force <device>",
        ),
    ]


def usable_methods() -> List[EraseMethod]:
    return [m for m in list_methods() if m.available]


def get_method(method_id: str) -> EraseMethod:
    for m in list_methods():
        if m.id == method_id:
            return m
    raise KeyError(method_id)


def build_command(method: EraseMethod, drive: Drive) -> List[str]:
    """Return the exact argv list for the chosen method and drive."""
    p = drive.path
    if method.id == "wipefs_signatures":
        return ["wipefs", "--all", "--force", p]
    if method.id == "blkdiscard_discard":
        return ["blkdiscard", p]
    if method.id == "nist_clear":
        # zero pass only (-n 0), then -z writes zeros
        return ["shred", "-v", "-n", "0", "-z", p]
    if method.id == "dod_3pass":
        return ["shred", "-v", "-n", "3", "-z", p]
    if method.id == "dod_7pass":
        return ["shred", "-v", "-n", "7", "-z", p]
    if method.id == "gutmann_35pass":
        return ["shred", "-v", "-n", "35", p]
    raise RuntimeError("No command is defined for erase method: %s" % method.id)
