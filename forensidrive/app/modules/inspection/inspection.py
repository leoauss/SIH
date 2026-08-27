import tkinter as tk

from core.errors import AppError
from core.storage import list_drives
from models.drive import Drive
from modules.inspection.drive_details import DriveDetailsView
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import DriveCard, GhostButton, PrimaryButton, ScrollBody, TechnicalDetails


class InspectionView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        tk.Label(self, text="Inspect a storage drive", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(
            self,
            text="Choose the drive you want to work with. You do not need to type a name.",
            bg=Theme.BG,
            fg=Theme.MUTED,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(4, 12))
        self.banner = Banner(self)
        toolbar = tk.Frame(self, bg=Theme.BG)
        toolbar.pack(fill="x", pady=(0, 8))
        GhostButton(toolbar, "Look again", command=self.refresh).pack(side="left")
        self.body = ScrollBody(self)
        self.body.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        for child in self.body.inner.winfo_children():
            child.destroy()
        self.banner.clear()
        try:
            drives = list_drives()
        except AppError as exc:
            self.banner.show(exc.user_message, "error")
            details = TechnicalDetails(self.body.inner)
            details.pack(fill="x", pady=8)
            details.set_text(exc.combined_technical())
            return
        if not drives:
            self.banner.show("No storage drives were found.", "warn")
            return
        for drive in drives:
            card = DriveCard(self.body.inner, drive)
            card.pack(fill="x", pady=8)
            PrimaryButton(card, "View Details", command=lambda d=drive: self.open_details(d)).pack(anchor="w", padx=16, pady=(0, 12))

    def open_details(self, drive: Drive):
        for child in self.winfo_children():
            child.destroy()
        DriveDetailsView(self, self.app, drive).pack(fill="both", expand=True)
