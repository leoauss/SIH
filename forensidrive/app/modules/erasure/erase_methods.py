import tkinter as tk

from integrations.erasure_tools import EraseMethod, list_methods
from models.drive import Drive
from modules.erasure.confirmation import ConfirmationView
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody


class EraseMethodsView(tk.Frame):
    def __init__(self, master, app, drive: Drive):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        tk.Label(self, text="Choose how to erase", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        identity = "Selected drive: %s    %s    %s" % (drive.display_title(), drive.size_label, drive.path)
        tk.Label(self, text=identity, bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(4, 16))
        body = ScrollBody(self)
        body.pack(fill="both", expand=True)
        methods = list_methods()
        if not any(m.available for m in methods):
            tk.Label(
                body.inner,
                text="No erase tools were found on this computer. ForensiDrive will not guess a command.",
                bg=Theme.BG,
                fg=Theme.MUTED,
                wraplength=800,
                justify="left",
            ).pack(anchor="w")
        for method in methods:
            card = tk.Frame(body.inner, bg=Theme.SURFACE)
            card.pack(fill="x", pady=8)
            tk.Label(card, text=method.title, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 15, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
            tk.Label(card, text=method.summary, bg=Theme.SURFACE, fg=Theme.MUTED, wraplength=800, justify="left").pack(anchor="w", padx=16)
            tk.Label(card, text=method.warning, bg=Theme.SURFACE, fg=Theme.ACCENT_DANGER, wraplength=800, justify="left").pack(anchor="w", padx=16, pady=(4, 0))
            if method.available:
                PrimaryButton(card, "Continue", command=lambda m=method: self._continue(m), danger=True).pack(anchor="w", padx=16, pady=12)
            else:
                tk.Label(card, text=method.missing_message(), bg=Theme.SURFACE, fg=Theme.MUTED, wraplength=800, justify="left").pack(anchor="w", padx=16, pady=12)
        GhostButton(self, "Choose a different drive", command=self.app.show_erasure).pack(anchor="w", pady=12)

    def _continue(self, method: EraseMethod):
        for child in self.winfo_children():
            child.destroy()
        ConfirmationView(self, self.app, self.drive, method).pack(fill="both", expand=True)
