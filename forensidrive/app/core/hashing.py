"""Device and file hashing for pre/post operation integrity checks."""

import hashlib
import os
from typing import Callable, Optional

from core.commands import command_exists, run_command

CHUNK_SIZE = 64 * 1024 * 1024  # 64 MB per read


def hash_file(path: str, algorithm: str = "sha256") -> str:
    """
    Hash a regular file using Python hashlib.
    Returns lowercase hex digest, or empty string on error.
    """
    try:
        h = hashlib.new(algorithm)
        with open(path, "rb") as fh:
            while True:
                chunk = fh.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, ValueError):
        return ""


def hash_device(
    path: str,
    algorithm: str = "sha256",
    on_progress: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Hash a block device or file.

    Strategy:
      1. If it is a plain file (demo mode / tests) use hash_file() directly.
      2. If on Linux with sha256sum available, pipe dd output through it
         for correct block-device handling.
      3. Otherwise fall back to Python open() — slower but portable.

    on_progress(message) is called periodically so the UI can show activity.
    Returns lowercase hex digest or empty string on failure.
    """
    if not os.path.exists(path) or os.path.isfile(path):
        return hash_file(path, algorithm)

    tool = algorithm + "sum"
    if command_exists("dd") and command_exists(tool):
        if on_progress:
            on_progress("Reading device with dd | %s ..." % tool)
        result = run_command(
            ["bash", "-c", "dd if=%s bs=64M 2>/dev/null | %s" % (path, tool)],
            timeout=1800,
            user_error="We couldn't fingerprint the drive.",
        )
        if result.ok and result.stdout.strip():
            # Output format: "<digest>  -\n"
            parts = result.stdout.strip().split()
            if parts:
                return parts[0]

    # Python fallback
    if on_progress:
        on_progress("Reading device (Python fallback) ...")
    return hash_file(path, algorithm)


def format_hash(digest: str) -> str:
    """Return a compact display string: first 16 chars ... last 8 chars."""
    if not digest:
        return "unavailable"
    if len(digest) <= 24:
        return digest
    return "%s...%s" % (digest[:16], digest[-8:])
