import tkinter as tk

from integrations.recovery_tools import RecoveryMethod, list_methods
from models.drive import Drive
from modules.recovery.recovery_scan import RecoveryScanView
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody


class RecoveryToolsView(tk.Frame):
    def __init__(self, master, app, drive: Drive):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        tk.Label(self, text="What should we look for?", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(
            self,
            text="Searching: %s (%s)" % (drive.display_title(), drive.path),
            bg=Theme.BG,
            fg=Theme.MUTED,
        ).pack(anchor="w", pady=(4, 16))
        body = ScrollBody(self)
        body.pack(fill="both", expand=True)
        methods = list_methods()
        usable = [m for m in methods if m.available]
        if not usable:
            tk.Label(
                body.inner,
                text="No recovery tools were found on this computer. ForensiDrive does not invent its own recovery method.",
                bg=Theme.BG,
                fg=Theme.MUTED,
                wraplength=800,
                justify="left",
            ).pack(anchor="w")
        for method in methods:
            self._method_card(body.inner, method)
        GhostButton(self, "Choose a different drive", command=self.app.show_recovery).pack(anchor="w", pady=12)

    def _method_card(self, parent, method: RecoveryMethod):
        card = tk.Frame(parent, bg=Theme.SURFACE)
        card.pack(fill="x", pady=8)
        tk.Label(card, text=method.title, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 15, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
        tk.Label(card, text=method.summary, bg=Theme.SURFACE, fg=Theme.MUTED, wraplength=800, justify="left").pack(anchor="w", padx=16)
        if method.available:
            PrimaryButton(card, "Continue", command=lambda m=method: self._continue(m)).pack(anchor="w", padx=16, pady=12)
        else:
            tk.Label(card, text=method.missing_message() if method.id != "testdisk_not_wired" else method.notes, bg=Theme.SURFACE, fg=Theme.MUTED, wraplength=800, justify="left").pack(anchor="w", padx=16, pady=12)

    def _continue(self, method: RecoveryMethod):
        for child in self.winfo_children():
            child.destroy()
        RecoveryScanView(self, self.app, self.drive, method).pack(fill="both", expand=True)
