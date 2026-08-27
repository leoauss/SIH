"""Host and application information."""

import os
import platform
from pathlib import Path

from core.commands import command_exists, run_command

APP_VERSION = "0.1.0"
APP_NAME = "ForensiDrive"


def install_root() -> Path:
    env = os.environ.get("FORENSIDRIVE_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def app_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().strip()
    except OSError:
        return ""


def kernel_version() -> str:
    return platform.release() or "unknown"


def cpu_architecture() -> str:
    return platform.machine() or "unknown"


def available_ram_label() -> str:
    meminfo = _read_text("/proc/meminfo")
    for line in meminfo.splitlines():
        if line.startswith("MemAvailable:") or line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    kib = int(parts[1])
                except ValueError:
                    continue
                mib = kib / 1024.0
                if mib >= 1024:
                    return "%.1f GB" % (mib / 1024.0)
                return "%.0f MB" % mib
    if command_exists("free"):
        result = run_command(["free", "-h"], timeout=5)
        if result.ok:
            return result.stdout.strip().splitlines()[0] if False else _parse_free(result.stdout)
    return "unknown"


def _parse_free(text: str) -> str:
    for line in text.splitlines():
        if line.lower().startswith("mem:"):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
    return "unknown"


def boot_mode() -> str:
    if os.path.isdir("/sys/firmware/efi"):
        return "UEFI"
    if os.name == "posix":
        return "Legacy (BIOS) or unknown"
    return "unknown"


def collect_system_info() -> dict:
    from integrations.systemrescue import systemrescue_version

    return {
        "application": APP_NAME,
        "application_version": APP_VERSION,
        "systemrescue_version": systemrescue_version(),
        "kernel": kernel_version(),
        "architecture": cpu_architecture(),
        "memory": available_ram_label(),
        "boot_mode": boot_mode(),
        "install_root": str(install_root()),
    }
