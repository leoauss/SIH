"""Metadata stripping and filesystem flush adapters."""

from core.commands import CommandResult, command_exists, run_command


def has_mat2() -> bool:
    return command_exists("mat2")


def has_exiftool() -> bool:
    return command_exists("exiftool")


def strip_metadata(path: str) -> CommandResult:
    """
    Remove embedded metadata from a file before secure deletion.
    Prefers mat2 (handles many formats), falls back to exiftool.
    Returns a CommandResult describing what happened.
    """
    if command_exists("mat2"):
        return run_command(
            ["mat2", "--inplace", path],
            timeout=30,
            user_error="We couldn't remove metadata from the file.",
        )
    if command_exists("exiftool"):
        return run_command(
            ["exiftool", "-all=", "-overwrite_original", path],
            timeout=30,
            user_error="We couldn't remove metadata from the file.",
        )
    # Neither tool available; return a synthetic result
    return CommandResult(
        argv=["mat2", path],
        returncode=127,
        stdout="",
        stderr="No metadata stripping tool (mat2 or exiftool) was found.",
        missing=True,
    )


def sync_and_flush() -> CommandResult:
    """
    Flush write buffers to disk and drop page cache.
    Ensures overwritten data is committed before we consider the job done.
    """
    return run_command(
        ["bash", "-c", "sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || sync"],
        timeout=30,
        user_error="We couldn't flush the disk write cache.",
    )
