import tkinter as tk

from core.filesystem import summarize_access
from models.drive import Drive
from models.partition import Partition
from ui.theme import Theme
from ui.widgets import GhostButton


class PartitionDetailsView(tk.Frame):
    def __init__(self, master, app, drive: Drive, partition: Partition):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        tk.Label(self, text=partition.display_title(), bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self, text="On drive %s" % drive.display_title(), bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(0, 16))
        facts = [
            ("Size", partition.size_label),
            ("File format", partition.filesystem_label()),
            ("Files currently accessible", summarize_access(partition)),
            ("Drive path", partition.path),
        ]
        for label, value in facts:
            row = tk.Frame(self, bg=Theme.SURFACE)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=Theme.SURFACE, fg=Theme.MUTED).pack(anchor="w", padx=14, pady=(8, 0))
            tk.Label(row, text=value, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 14, "bold"), wraplength=800, justify="left").pack(anchor="w", padx=14, pady=(0, 8))
        GhostButton(self, "Back to drive list", command=self.app.show_inspection).pack(anchor="w", pady=16)
