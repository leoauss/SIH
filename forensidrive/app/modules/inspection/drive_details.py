import tkinter as tk

from models.drive import Drive
from modules.inspection.partition_details import PartitionDetailsView
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody


class DriveDetailsView(tk.Frame):
    def __init__(self, master, app, drive: Drive):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        tk.Label(self, text=drive.display_title(), bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self, text="%s    %s" % (drive.size_label, drive.path), bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(0, 12))

        facts = [
            ("Size", drive.size_label),
            ("Maker", drive.vendor or "unknown"),
            ("Model", drive.model or "unknown"),
            ("Can be unplugged", "Yes" if drive.removable else "No"),
            ("Locked against changes", "Yes" if drive.read_only else "No"),
            ("Connection", drive.transport or "unknown"),
        ]
        for label, value in facts:
            row = tk.Frame(self, bg=Theme.SURFACE)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=Theme.SURFACE, fg=Theme.MUTED).pack(anchor="w", padx=14, pady=(8, 0))
            tk.Label(row, text=value, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 14, "bold")).pack(anchor="w", padx=14, pady=(0, 8))

        tk.Label(self, text="Areas on this drive", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 16, "bold")).pack(anchor="w", pady=(16, 8))
        body = ScrollBody(self)
        body.pack(fill="both", expand=True)
        if not drive.partitions:
            tk.Label(body.inner, text="No separate areas were found on this drive.", bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w")
        for partition in drive.partitions:
            card = tk.Frame(body.inner, bg=Theme.SURFACE)
            card.pack(fill="x", pady=6)
            tk.Label(card, text=partition.display_title(), bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 14, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
            tk.Label(card, text="%s    %s" % (partition.size_label, partition.path), bg=Theme.SURFACE, fg=Theme.MUTED).pack(anchor="w", padx=14)
            PrimaryButton(card, "View this area", command=lambda p=partition: self.open_partition(p)).pack(anchor="w", padx=14, pady=10)

        buttons = tk.Frame(self, bg=Theme.BG)
        buttons.pack(fill="x", pady=12)
        GhostButton(buttons, "Back to drive list", command=self.app.show_inspection).pack(side="left")

    def open_partition(self, partition):
        for child in self.winfo_children():
            child.destroy()
        PartitionDetailsView(self, self.app, self.drive, partition).pack(fill="both", expand=True)
