import tkinter as tk

from integrations.recovery_tools import RecoveryMethod
from models.drive import Drive
from models.operation import Operation, OperationStatus
from ui.theme import Theme
from ui.widgets import PrimaryButton, TechnicalDetails


class RecoveryResultsView(tk.Frame):
    def __init__(self, master, app, drive: Drive, method: RecoveryMethod, operation: Operation, destination: str):
        super().__init__(master, bg=Theme.BG)
        self.app = app
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
        tk.Label(self, text="Method: %s" % method.title, bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(0, 12))
        details = TechnicalDetails(self)
        details.pack(fill="both", expand=True, pady=8)
        details.set_text("\n".join(operation.technical_lines))
        PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=12)
