import os
import subprocess
import tkinter as tk
from typing import Optional

from core.audit import log_event
from core.classifier import ClassificationReport
from core.reporting import generate_recovery_report
from integrations.recovery_tools import RecoveryMethod
from models.audit_event import AuditEvent
from models.drive import Drive
from models.operation import Operation, OperationStatus
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, TechnicalDetails


class RecoveryResultsView(tk.Frame):
    def __init__(
        self,
        master,
        app,
        drive: Drive,
        method: RecoveryMethod,
        operation: Operation,
        destination: str,
        classification: Optional[ClassificationReport] = None,
        chain_of_custody_path: Optional[str] = None,
    ):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.method = method
        self.operation = operation
        self.destination = destination
        self.classification = classification
        self.chain_of_custody_path = chain_of_custody_path
        self._report_path = None

        if operation.status == OperationStatus.SUCCEEDED:
            title = "Recovery finished"
            summary = "The operation completed successfully. Check the folder you chose for recovered files."
            color = Theme.ACCENT_OK
        elif operation.status == OperationStatus.CANCELLED:
            title = "Recovery stopped"
            summary = "The operation was cancelled."
            color = Theme.MUTED
        else:
            title = "We couldn't complete this operation."
            summary = operation.user_message or "Recovery did not finish as expected."
            color = Theme.ACCENT_DANGER

        tk.Label(self, text=title, bg=Theme.BG, fg=color, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self, text=summary, bg=Theme.BG, fg=Theme.TEXT, wraplength=900, justify="left").pack(anchor="w", pady=(8, 8))
        tk.Label(self, text="Drive: %s (%s)" % (drive.display_title(), drive.path), bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w")
        tk.Label(self, text="Saved to: %s" % (destination or "not chosen"), bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w")
        tk.Label(self, text="Method: %s" % method.title, bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(0, 8))

        # Classification & Evidence Card
        if classification and classification.total_files > 0:
            summary_card = tk.Frame(self, bg=Theme.SURFACE)
            summary_card.pack(fill="x", pady=4)
            tk.Label(
                summary_card,
                text="Recovered Files Summary (%d total files)" % classification.total_files,
                bg=Theme.SURFACE,
                fg=Theme.TEXT,
                font=(Theme.FONT, 13, "bold"),
            ).pack(anchor="w", padx=16, pady=(10, 4))

            cat_str = ", ".join("%s: %d" % (cat.capitalize(), count) for cat, count in sorted(classification.by_category.items()))
            tk.Label(summary_card, text=cat_str, bg=Theme.SURFACE, fg=Theme.MUTED, wraplength=850, justify="left").pack(anchor="w", padx=16)

            conf_str = "Confidence: %d High, %d Medium, %d Low" % (
                classification.high_confidence,
                classification.medium_confidence,
                classification.low_confidence,
            )
            tk.Label(summary_card, text=conf_str, bg=Theme.SURFACE, fg=Theme.ACCENT, font=(Theme.FONT, 10)).pack(anchor="w", padx=16, pady=(2, 10))

        if chain_of_custody_path:
            tk.Label(
                self,
                text="Forensic Chain of Custody written to: %s" % chain_of_custody_path,
                bg=Theme.BG,
                fg=Theme.MUTED,
                font=(Theme.FONT, 10),
            ).pack(anchor="w", pady=(2, 6))

        # Action Buttons
        btn_bar = tk.Frame(self, bg=Theme.BG)
        btn_bar.pack(fill="x", pady=4)

        if destination and os.path.exists(destination):
            GhostButton(btn_bar, "Open Output Folder", command=self._open_dest).pack(side="left", padx=(0, 8))

        GhostButton(btn_bar, "Generate Forensic Report", command=self._generate_report).pack(side="left", padx=(0, 8))

        self.report_label = tk.Label(self, text="", bg=Theme.BG, fg=Theme.ACCENT_OK, font=(Theme.FONT, 10))
        self.report_label.pack(anchor="w", pady=(2, 4))

        details = TechnicalDetails(self)
        details.pack(fill="both", expand=True, pady=8)
        details.set_text("\n".join(operation.technical_lines))

        PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=8)

    def _open_dest(self):
        if not self.destination or not os.path.exists(self.destination):
            return
        try:
            if os.name == "nt":
                os.startfile(self.destination)
            else:
                subprocess.Popen(["xdg-open", self.destination])
        except Exception:
            pass

    def _generate_report(self):
        event = AuditEvent(
            kind="recovery",
            drive_path=self.drive.path,
            serial=self.drive.serial,
            method_id=self.method.id,
            method_title=self.method.title,
            status=self.operation.status.value,
            user_message=self.operation.user_message,
            hash_before=self.operation.hash_before or "",
            destination=self.destination,
            files_recovered=self.classification.total_files if self.classification else 0,
            technical_lines=self.operation.technical_lines,
        )
        report_path = generate_recovery_report(event, self.classification)
        self._report_path = report_path
        self.report_label.configure(text="Forensic report generated: %s" % report_path)
