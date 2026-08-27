"""Filesystem command adapters. GUI must not build these commands."""

from core.commands import CommandResult, command_exists, run_command


def unmount_path(target: str) -> CommandResult:
    if command_exists("umount"):
        return run_command(
            ["umount", target],
            timeout=30,
            user_error="We couldn't close the drive before continuing.",
        )
    if command_exists("udisksctl"):
        return run_command(
            ["udisksctl", "unmount", "-b", target],
            timeout=30,
            user_error="We couldn't close the drive before continuing.",
        )
    return CommandResult(
        argv=["umount", target],
        returncode=127,
        stdout="",
        stderr="No unmount tool was found.",
        missing=True,
    )


def find_mount(target: str) -> CommandResult:
    if command_exists("findmnt"):
        return run_command(
            ["findmnt", "-n", "-o", "TARGET", target],
            timeout=10,
            user_error="We couldn't check whether files are currently accessible.",
        )
    return CommandResult(
        argv=["findmnt", target],
        returncode=127,
        stdout="",
        stderr="findmnt is not available.",
        missing=True,
    )
