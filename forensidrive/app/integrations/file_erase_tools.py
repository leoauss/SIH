"""Per-file and per-folder secure deletion adapters. GUI must not build these commands."""

from dataclasses import dataclass
from typing import List

from core.commands import command_exists


@dataclass
class FileEraseMethod:
    id: str
    title: str
    summary: str
    warning: str
    tool: str
    available: bool
    notes: str = ""
    recursive: bool = True   # supports folders

    def missing_message(self) -> str:
        return (
            "This option is not available because the '%s' tool was not found." % self.tool
        )


def list_file_methods() -> List[FileEraseMethod]:
    shred_ok = command_exists("shred")
    srm_ok = command_exists("srm")
    wipe_ok = command_exists("wipe")

    return [
        FileEraseMethod(
            id="shred_file",
            title="Overwrite and delete (shred)",
            summary="Overwrite each file three times with random data, then delete it.",
            warning="Does not remove filename from directory journal. Metadata stripping is applied separately.",
            tool="shred",
            available=shred_ok,
            notes="Runs: shred -v -u -n 3 <file>",
        ),
        FileEraseMethod(
            id="srm_file",
            title="Secure remove (srm)",
            summary="Securely delete files using the secure-delete suite. Handles filenames and directory entries.",
            warning="ForensiDrive does not guarantee complete removal on journalled filesystems.",
            tool="srm",
            available=srm_ok,
            notes="Runs: srm -r -z <path>",
        ),
        FileEraseMethod(
            id="wipe_file",
            title="Wipe (wipe tool)",
            summary="Overwrite files using the dedicated wipe utility with its default pass count.",
            warning="ForensiDrive does not guarantee complete removal on journalled filesystems.",
            tool="wipe",
            available=wipe_ok,
            notes="Runs: wipe -r -f <path>",
        ),
        FileEraseMethod(
            id="python_zero",
            title="Zero and delete (built-in fallback)",
            summary="Write zeros over each file using Python, then delete it. Available without any extra tools.",
            warning="Does not remove filenames from journal. Slower than dedicated tools. Use only as a last resort.",
            tool="python",
            available=True,
            notes="Uses Python open(path, 'r+b') + os.unlink()",
        ),
    ]


def usable_file_methods() -> List[FileEraseMethod]:
    return [m for m in list_file_methods() if m.available]


def build_file_command(method: FileEraseMethod, path: str) -> List[str]:
    """Return argv for erasing a single file."""
    if method.id == "shred_file":
        return ["shred", "-v", "-u", "-n", "3", path]
    if method.id == "srm_file":
        return ["srm", "-z", path]
    if method.id == "wipe_file":
        return ["wipe", "-f", path]
    if method.id == "python_zero":
        # Caller handles this specially — return empty list as signal
        return []
    raise RuntimeError("No command defined for file erase method: %s" % method.id)


def build_folder_command(method: FileEraseMethod, folder: str) -> List[str]:
    """Return argv for erasing a folder recursively."""
    if method.id == "shred_file":
        # shred does not recurse; caller must enumerate files
        return []
    if method.id == "srm_file":
        return ["srm", "-r", "-z", folder]
    if method.id == "wipe_file":
        return ["wipe", "-r", "-f", folder]
    if method.id == "python_zero":
        return []
    raise RuntimeError("No command defined for folder erase method: %s" % method.id)
