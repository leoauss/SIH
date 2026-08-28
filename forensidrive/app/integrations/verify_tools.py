"""Post-erase verification helpers. Read back sampled blocks to check expected pattern."""

from dataclasses import dataclass
from typing import List

from core.commands import command_exists, run_command


@dataclass
class VerifyResult:
    passed: bool
    samples_checked: int
    non_zero_blocks: int
    technical: str


def verify_zeros(device_path: str, sample_count: int = 10) -> VerifyResult:
    """
    Sample random blocks from the device and check they are all zeros.
    Uses Python to read block-device bytes directly when possible.
    Returns a VerifyResult; never raises.
    """
    import os
    import random

    BLOCK = 512 * 1024  # 512 KB sample size

    try:
        size = os.path.getsize(device_path) if os.path.isfile(device_path) else _device_size(device_path)
    except OSError:
        return VerifyResult(passed=False, samples_checked=0, non_zero_blocks=0,
                            technical="Could not determine device size.")

    if size <= 0:
        return VerifyResult(passed=False, samples_checked=0, non_zero_blocks=0,
                            technical="Device reports zero size.")

    offsets: List[int] = []
    if size > BLOCK:
        for _ in range(sample_count):
            max_offset = size - BLOCK
            offsets.append(random.randint(0, max_offset) // 512 * 512)
    else:
        offsets = [0]

    non_zero = 0
    checked = 0
    lines: List[str] = []
    try:
        with open(device_path, "rb") as fh:
            for offset in offsets:
                fh.seek(offset)
                chunk = fh.read(BLOCK)
                checked += 1
                if any(b != 0 for b in chunk):
                    non_zero += 1
                    lines.append("Non-zero data found at offset %d" % offset)
                else:
                    lines.append("Block at offset %d: all zeros OK" % offset)
    except OSError as exc:
        return VerifyResult(passed=False, samples_checked=checked, non_zero_blocks=non_zero,
                            technical=str(exc))

    passed = non_zero == 0
    summary = "Verified %d blocks. Non-zero: %d. Result: %s" % (
        checked, non_zero, "PASS" if passed else "FAIL"
    )
    return VerifyResult(
        passed=passed,
        samples_checked=checked,
        non_zero_blocks=non_zero,
        technical=summary + "\n" + "\n".join(lines),
    )


def _device_size(path: str) -> int:
    """Return device size in bytes by reading /sys or using blockdev."""
    import os
    # Try /sys/block
    name = os.path.basename(path)
    sys_size = "/sys/block/%s/size" % name
    try:
        with open(sys_size) as f:
            return int(f.read().strip()) * 512
    except (OSError, ValueError):
        pass
    # Try blockdev
    if command_exists("blockdev"):
        result = run_command(["blockdev", "--getsize64", path], timeout=10)
        if result.ok and result.stdout.strip().isdigit():
            return int(result.stdout.strip())
    return 0
