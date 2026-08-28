"""Append-only structured audit log. One JSON Lines record per operation."""

import json
import os
from pathlib import Path
from typing import List

from models.audit_event import AuditEvent


def get_log_dir() -> Path:
    """Return the directory where audit logs and reports are stored."""
    env = os.environ.get("FORENSIDRIVE_LOG_DIR")
    if env:
        return Path(env)
    # Prefer /var/log on a live Linux system; fall back to home dir
    candidate = Path("/var/log/forensidrive")
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except OSError:
        pass
    return Path.home() / ".forensidrive" / "logs"


def get_log_path() -> Path:
    log_dir = get_log_dir()
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return log_dir / "audit.jsonl"


def get_reports_dir() -> Path:
    reports = get_log_dir() / "reports"
    try:
        reports.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return reports


def log_event(event: AuditEvent) -> None:
    """Append one audit record to the log file. Never raises — UI must not crash."""
    path = get_log_path()
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
    except OSError:
        pass


def read_events() -> List[AuditEvent]:
    """Read all past audit events from the log file, newest last."""
    path = get_log_path()
    events: List[AuditEvent] = []
    if not path.exists():
        return events
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    events.append(AuditEvent.from_dict(data))
                except (json.JSONDecodeError, TypeError):
                    continue
    except OSError:
        pass
    return events
