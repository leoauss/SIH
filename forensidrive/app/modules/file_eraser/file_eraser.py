import tkinter as tk

from core.errors import AppError
from core.storage import list_drives
from models.drive import Drive
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import DriveCard, PrimaryButton, ScrollBody, TechnicalDetails


class FileEraserView(tk.Frame):
    """Entry screen: choose a drive whose files you want to erase."""

    def __init__(self, master, app):
        super().__init__(master, bg=Theme.BG)
        self.app = app

        tk.Label(self, text="Erase files and folders", bg=Theme.BG, fg=Theme.TEXT,
                 font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(
            self,
            text=(
                "Choose the drive that contains the files you want to delete permanently. "
                "This will let you pick individual files and folders on that drive."
            ),
            bg=Theme.BG, fg=Theme.MUTED, wraplength=900, justify="left",
        ).pack(anchor="w", pady=(4, 12))

        self.banner = Banner(self)
        self.body = ScrollBody(self)
        self.body.pack(fill="both", expand=True)
        self._load()

    def _load(self):
        try:
            drives = list_drives()
        except AppError as exc:
            self.banner.show(exc.user_message, "error")
            details = TechnicalDetails(self.body.inner)
            details.pack(fill="x")
            details.set_text(exc.combined_technical())
            return
        if not drives:
            self.banner.show("No storage drives were found.", "warn")
            return
        for drive in drives:
            card = DriveCard(self.body.inner, drive)
            card.pack(fill="x", pady=8)
            PrimaryButton(card, "Choose files on this drive",
                          command=lambda d=drive: self._choose(d),
                          danger=True).pack(anchor="w", padx=16, pady=(0, 12))

    def _choose(self, drive: Drive):
        for child in self.winfo_children():
            child.destroy()
        from modules.file_eraser.file_target_view import FileTargetView
        FileTargetView(self, self.app, drive).pack(fill="both", expand=True)
