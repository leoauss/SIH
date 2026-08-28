import os
import subprocess
import tkinter as tk
from tkinter import ttk

from core.audit import get_reports_dir, read_events
from core.reporting import generate_erasure_report, generate_file_erase_report, generate_recovery_report
from models.audit_event import AuditEvent
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody, TechnicalDetails


class AuditView(tk.Frame):
    """Displays past audit events in a table with report generation."""

    def __init__(self, master, app):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self._events = []

        tk.Label(self, text="Audit log", bg=Theme.BG, fg=Theme.TEXT,
                 font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self, text="A record of all operations performed by ForensiDrive.",
                 bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(4, 12))

        # Toolbar
        toolbar = tk.Frame(self, bg=Theme.BG)
        toolbar.pack(fill="x", pady=(0, 8))
        GhostButton(toolbar, "Refresh", command=self._load).pack(side="left", padx=(0, 8))
        self.report_btn = GhostButton(toolbar, "Generate report for selected",
                                      command=self._generate_report)
        self.report_btn.pack(side="left", padx=(0, 8))
        self.open_btn = GhostButton(toolbar, "Open report", command=self._open_report)
        self.open_btn.pack(side="left")

        # Table
        cols = ("timestamp", "kind", "target", "method", "status")
        frame = tk.Frame(self, bg=Theme.SURFACE)
        frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                 selectmode="browse", height=16)
        self.tree.heading("timestamp", text="Timestamp (UTC)")
        self.tree.heading("kind",      text="Operation")
        self.tree.heading("target",    text="Drive / Target")
        self.tree.heading("method",    text="Method")
        self.tree.heading("status",    text="Status")
        self.tree.column("timestamp", width=200)
        self.tree.column("kind",      width=140)
        self.tree.column("target",    width=220)
        self.tree.column("method",    width=200)
        self.tree.column("status",    width=100, anchor="center")
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Detail
        self.detail_var = tk.StringVar(value="Select a row to see details.")
        tk.Label(self, textvariable=self.detail_var, bg=Theme.BG, fg=Theme.MUTED,
                 font=(Theme.FONT, 10), wraplength=900, justify="left").pack(anchor="w", pady=8)

        GhostButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=4)

        self._last_report_path = None
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        self._events = list(reversed(read_events()))  # newest first
        for event in self._events:
            ts = event.timestamp[:19].replace("T", " ") if event.timestamp else ""
            kind_label = {"erasure": "Drive Erase", "recovery": "Recovery",
                          "file_erase": "File Erase"}.get(event.kind, event.kind)
            target = event.drive_path or event.destination or "-"
            status_upper = event.status.upper() if event.status else "-"
            self.tree.insert("", "end", iid=event.id,
                             values=(ts, kind_label, target, event.method_title, status_upper))

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        event_id = sel[0]
        event = next((e for e in self._events if e.id == event_id), None)
        if event:
            self.detail_var.set(
                "ID: %s    Hash before: %s    Files: erased=%d failed=%d recovered=%d" % (
                    event.id[:8],
                    (event.hash_before[:16] + "...") if event.hash_before else "n/a",
                    event.files_erased, event.files_failed, event.files_recovered,
                ))

    def _selected_event(self):
        sel = self.tree.selection()
        if not sel:
            return None
        event_id = sel[0]
        return next((e for e in self._events if e.id == event_id), None)

    def _generate_report(self):
        event = self._selected_event()
        if not event:
            return
        if event.kind == "erasure":
            path = generate_erasure_report(event)
        elif event.kind == "recovery":
            path = generate_recovery_report(event)
        else:
            path = generate_file_erase_report(event)
        self._last_report_path = path
        self.detail_var.set("Report saved: %s" % path)

    def _open_report(self):
        path = self._last_report_path
        if not path or not path.exists():
            self.detail_var.set("Generate a report first, then click Open report.")
            return
        try:
            if os.name == "nt":
                os.startfile(str(path))
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            self.detail_var.set("Could not open report: %s" % exc)
