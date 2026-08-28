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

        tk.Label(self, text="Choose how to erase", bg=Theme.BG, fg=Theme.TEXT,
                 font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        identity = "Selected drive: %s    %s    %s" % (
            drive.display_title(), drive.size_label, drive.path)
        tk.Label(self, text=identity, bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(4, 4))

        # Drive type badge
        kind = "Solid-state drive (SSD/NVMe)" if drive.is_ssd() else "Rotational hard drive (HDD)"
        tk.Label(self, text="Drive type detected: %s" % kind,
                 bg=Theme.BG, fg=Theme.ACCENT, font=(Theme.FONT, 11)).pack(anchor="w", pady=(0, 16))

        body = ScrollBody(self)
        body.pack(fill="both", expand=True)

        methods = list_methods()
        recommended_id = drive.recommended_erase_standard()

        if not any(m.available for m in methods):
            tk.Label(body.inner,
                     text="No erase tools were found on this computer. ForensiDrive will not guess a command.",
                     bg=Theme.BG, fg=Theme.MUTED, wraplength=800, justify="left").pack(anchor="w")

        for method in methods:
            self._method_card(body.inner, method, recommended=method.id == recommended_id)

        GhostButton(self, "Choose a different drive", command=self.app.show_erasure).pack(anchor="w", pady=12)

    def _method_card(self, parent, method: EraseMethod, recommended: bool):
        border_colour = Theme.ACCENT if recommended else Theme.BORDER
        card = tk.Frame(parent, bg=Theme.SURFACE, highlightthickness=2,
                        highlightbackground=border_colour)
        card.pack(fill="x", pady=8)

        header = tk.Frame(card, bg=Theme.SURFACE)
        header.pack(fill="x", padx=16, pady=(12, 2))

        tk.Label(header, text=method.title, bg=Theme.SURFACE, fg=Theme.TEXT,
                 font=(Theme.FONT, 15, "bold")).pack(side="left")

        if recommended:
            tk.Label(header, text=" RECOMMENDED ", bg=Theme.ACCENT, fg="#ffffff",
                     font=(Theme.FONT, 9, "bold"), padx=6, pady=2).pack(side="left", padx=(10, 0))

        badge = method.compliance_label
        if badge:
            tk.Label(header, text=" %s " % badge, bg=Theme.SURFACE_ALT, fg=Theme.TEXT,
                     font=(Theme.FONT, 9), padx=6, pady=2).pack(side="left", padx=(8, 0))

        tk.Label(card, text=method.summary, bg=Theme.SURFACE, fg=Theme.MUTED,
                 wraplength=800, justify="left").pack(anchor="w", padx=16)
        tk.Label(card, text=method.warning, bg=Theme.SURFACE, fg=Theme.ACCENT_DANGER,
                 wraplength=800, justify="left").pack(anchor="w", padx=16, pady=(4, 0))

        # Standard details if available
        std = method.standard
        if std and std.passes > 0:
            detail = "Passes: %d    Pattern: %s    Verify: %s" % (
                std.passes,
                std.pattern_description or "see standard",
                "Yes" if std.verify else "No",
            )
            tk.Label(card, text=detail, bg=Theme.SURFACE, fg=Theme.MUTED,
                     font=(Theme.FONT, 10)).pack(anchor="w", padx=16, pady=(4, 0))

        if method.available:
            PrimaryButton(card, "Continue", command=lambda m=method: self._continue(m),
                          danger=True).pack(anchor="w", padx=16, pady=12)
        else:
            tk.Label(card, text=method.missing_message(), bg=Theme.SURFACE, fg=Theme.MUTED,
                     wraplength=800, justify="left").pack(anchor="w", padx=16, pady=12)

    def _continue(self, method: EraseMethod):
        for child in self.winfo_children():
            child.destroy()
        ConfirmationView(self, self.app, self.drive, method).pack(fill="both", expand=True)
