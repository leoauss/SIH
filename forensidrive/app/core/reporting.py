"""HTML forensic report generator. Zero external dependencies."""

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.audit import get_reports_dir
from core.hashing import format_hash
from core.system import APP_NAME, APP_VERSION
from models.audit_event import AuditEvent
from models.operation import Operation

_CSS = """
body{font-family:sans-serif;background:#0f1318;color:#e2e8f0;margin:0;padding:24px}
h1{color:#3d8bfd;border-bottom:2px solid #334155;padding-bottom:8px}
h2{color:#a8b3c1;margin-top:24px}
table{width:100%;border-collapse:collapse;margin:12px 0}
th{text-align:left;padding:8px 12px;background:#1b222b;color:#a8b3c1;font-size:0.85em;text-transform:uppercase}
td{padding:8px 12px;border-bottom:1px solid #334155}
.ok{color:#2f9e62;font-weight:bold}
.fail{color:#d64545;font-weight:bold}
.warn{color:#e09f3e;font-weight:bold}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.8em;font-weight:bold}
.badge-ok{background:#163527;color:#2f9e62}
.badge-fail{background:#3a1515;color:#d64545}
pre{background:#1b222b;padding:12px;border-radius:6px;white-space:pre-wrap;font-size:0.85em;color:#a8b3c1}
"""


def _html_wrap(title: str, body: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='utf-8'><title>%s</title>"
        "<style>%s</style></head><body>"
        "<h1>%s</h1>"
        "<p style='color:#a8b3c1;font-size:0.9em'>Generated: %s &nbsp;&bull;&nbsp; %s %s</p>"
        "%s"
        "</body></html>"
    ) % (html.escape(title), _CSS, html.escape(title), ts, APP_NAME, APP_VERSION, body)


def _kv_table(rows) -> str:
    rows_html = "".join(
        "<tr><th>%s</th><td>%s</td></tr>" % (html.escape(str(k)), html.escape(str(v)))
        for k, v in rows
    )
    return "<table>%s</table>" % rows_html


def generate_erasure_report(event: AuditEvent, operation: Optional[Operation] = None) -> Path:
    """Generate an HTML erasure report. Returns path to the file."""
    verify_note = event.notes or ""
    passed = "PASS" in verify_note.upper()
    verify_badge = (
        "<span class='badge badge-ok'>PASS</span>" if passed
        else "<span class='badge badge-fail'>FAIL / N/A</span>"
    )
    status_class = "ok" if event.status == "succeeded" else "fail"

    body = "<h2>Case Details</h2>"
    body += _kv_table([
        ("Case ID", event.id),
        ("Timestamp", event.timestamp),
        ("Kind", "Secure Drive Erasure"),
        ("Status", "<span class='%s'>%s</span>" % (status_class, event.status.upper())),
    ])

    body += "<h2>Drive Identity</h2>"
    body += _kv_table([
        ("Device path", event.drive_path),
        ("Serial number", event.serial or "unknown"),
    ])

    body += "<h2>Erasure Method</h2>"
    body += _kv_table([
        ("Method", event.method_title),
        ("Standard", event.standard_id or "none"),
        ("Compliance reference", _standard_ref(event.standard_id)),
    ])

    body += "<h2>Integrity</h2>"
    body += _kv_table([
        ("SHA-256 before erase", format_hash(event.hash_before) if event.hash_before else "not recorded"),
        ("Verification result", verify_badge),
        ("Verification notes", html.escape(verify_note)),
    ])

    if event.technical_lines:
        body += "<h2>Technical Log</h2><pre>%s</pre>" % html.escape("\n".join(event.technical_lines[-100:]))

    body += _footer_note()
    content = _html_wrap("Erasure Report — %s" % event.drive_path, body)
    out = get_reports_dir() / ("erasure_%s.html" % event.id[:8])
    try:
        out.write_text(content, encoding="utf-8")
    except OSError:
        pass
    return out


def generate_recovery_report(event: AuditEvent, classification=None) -> Path:
    """Generate an HTML recovery report. Returns path to the file."""
    status_class = "ok" if event.status == "succeeded" else "fail"

    body = "<h2>Case Details</h2>"
    body += _kv_table([
        ("Case ID", event.id),
        ("Timestamp", event.timestamp),
        ("Kind", "File Carving & Recovery"),
        ("Status", "<span class='%s'>%s</span>" % (status_class, event.status.upper())),
    ])

    body += "<h2>Source Drive</h2>"
    body += _kv_table([
        ("Device path", event.drive_path),
        ("Serial number", event.serial or "unknown"),
        ("SHA-256 (before recovery)", format_hash(event.hash_before) if event.hash_before else "not recorded"),
    ])

    body += "<h2>Recovery Method</h2>"
    body += _kv_table([
        ("Tool", event.method_title),
        ("Output folder", event.destination),
        ("Files recovered", event.files_recovered),
    ])

    if classification:
        body += "<h2>File Classification Summary</h2>"
        cat_rows = [(cat, count) for cat, count in sorted(classification.by_category.items())]
        cat_rows += [
            ("Total files", classification.total_files),
            ("HIGH confidence", classification.high_confidence),
            ("MEDIUM confidence", classification.medium_confidence),
            ("LOW confidence", classification.low_confidence),
        ]
        body += _kv_table(cat_rows)

    body += _footer_note()
    content = _html_wrap("Recovery Report — %s" % event.drive_path, body)
    out = get_reports_dir() / ("recovery_%s.html" % event.id[:8])
    try:
        out.write_text(content, encoding="utf-8")
    except OSError:
        pass
    return out


def generate_file_erase_report(event: AuditEvent) -> Path:
    """Generate an HTML file-erase report. Returns path to the file."""
    status_class = "ok" if event.status in ("succeeded", "partial") else "fail"

    body = "<h2>Case Details</h2>"
    body += _kv_table([
        ("Case ID", event.id),
        ("Timestamp", event.timestamp),
        ("Kind", "Secure File & Folder Erasure"),
        ("Status", "<span class='%s'>%s</span>" % (status_class, event.status.upper())),
    ])

    body += "<h2>Target Drive</h2>"
    body += _kv_table([
        ("Drive path", event.drive_path),
        ("Serial number", event.serial or "unknown"),
    ])

    body += "<h2>Results</h2>"
    body += _kv_table([
        ("Method", event.method_title),
        ("Files erased", event.files_erased),
        ("Files failed", event.files_failed),
    ])

    if event.technical_lines:
        body += "<h2>Technical Log</h2><pre>%s</pre>" % html.escape("\n".join(event.technical_lines[-100:]))

    body += _footer_note()
    content = _html_wrap("File Erase Report", body)
    out = get_reports_dir() / ("file_erase_%s.html" % event.id[:8])
    try:
        out.write_text(content, encoding="utf-8")
    except OSError:
        pass
    return out


def _standard_ref(standard_id: str) -> str:
    from core.standards import STANDARDS
    std = STANDARDS.get(standard_id)
    return std.reference if std else "None"


def _footer_note() -> str:
    return (
        "<hr style='border-color:#334155;margin-top:32px'>"
        "<p style='color:#a8b3c1;font-size:0.8em'>"
        "This report was generated automatically by %s %s. "
        "It records the actions taken by this software and does not constitute "
        "independent verification of erasure completeness or data recovery quality."
        "</p>" % (APP_NAME, APP_VERSION)
    )
