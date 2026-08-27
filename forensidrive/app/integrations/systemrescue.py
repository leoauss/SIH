"""SystemRescue live environment detection. No invented config keys."""

import os
from pathlib import Path

from core.commands import command_exists, run_command

KNOWN_OS_RELEASE = "/etc/os-release"
KNOWN_VERSION_FILES = (
    "/etc/systemrescue-release",
    "/usr/share/systemrescue/version",
    "/version",
)


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _os_release_fields() -> dict:
    fields = {}
    text = _read(KNOWN_OS_RELEASE)
    for line in text.splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        fields[key] = value.strip().strip('"')
    return fields


def systemrescue_version() -> str:
    for path in KNOWN_VERSION_FILES:
        text = _read(path)
        if text:
            return text.splitlines()[0]
    fields = _os_release_fields()
    pretty = fields.get("PRETTY_NAME") or fields.get("NAME")
    version = fields.get("VERSION") or fields.get("VERSION_ID")
    if pretty and "rescue" in pretty.lower():
        return pretty
    if pretty and version:
        return "%s %s" % (pretty, version)
    if pretty:
        return pretty
    if command_exists("uname"):
        result = run_command(["uname", "-a"], timeout=5)
        if result.ok:
            return "Not confirmed as SystemRescue. Kernel: %s" % result.stdout.strip()
    return "unknown"


def is_live_environment() -> bool:
    markers = (
        "/run/archiso",
        "/run/miso",
        "/etc/systemrescue",
    )
    return any(os.path.exists(path) for path in markers)


def detect_environment() -> dict:
    fields = _os_release_fields()
    pretty = fields.get("PRETTY_NAME") or ""
    likely = "systemrescue" in pretty.lower() or "sysrescue" in pretty.lower()
    if os.path.exists("/etc/systemrescue") or os.path.exists("/run/archiso"):
        likely = True
    return {
        "likely_systemrescue": likely,
        "live_environment": is_live_environment(),
        "os_pretty_name": pretty or "unknown",
        "version": systemrescue_version(),
        "graphical_session": bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")),
    }
