import tkinter as tk

from core.errors import AppError
from core.system import collect_system_info
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody, TechnicalDetails


class DashboardView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        tk.Label(self, text="What do you want to do?", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(
            self,
            text="Choose one of the options below. You do not need to type any drive names.",
            bg=Theme.BG,
            fg=Theme.MUTED,
            font=(Theme.FONT, 13),
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(0, 24))

        actions = [
            ("Recover Files", "Look for files that may still be on a drive.", self.app.show_recovery, False),
            ("Erase Drive", "Remove all information from a drive. Supports NIST 800-88, DoD 5220.22-M.", self.app.show_erasure, True),
            ("Erase Files & Folders", "Permanently delete specific files or folders and remove their traces.", self.app.show_file_eraser, True),
            ("Inspect Drive", "See which drives are connected and what they contain.", self.app.show_inspection, False),
            ("System Information", "See basic information about this computer and ForensiDrive.", self.app.show_system_info, False),
            ("View Audit Log", "See a record of all operations and generate forensic reports.", self.app.show_audit, False),
        ]
        for title, summary, command, danger in actions:
            card = tk.Frame(self, bg=Theme.SURFACE)
            card.pack(fill="x", pady=8)
            tk.Label(card, text=title, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 16, "bold")).pack(anchor="w", padx=18, pady=(14, 4))
            tk.Label(card, text=summary, bg=Theme.SURFACE, fg=Theme.MUTED, font=(Theme.FONT, 12), wraplength=800, justify="left").pack(anchor="w", padx=18)
            PrimaryButton(card, "Open", command=command, danger=danger).pack(anchor="w", padx=18, pady=14)

        GhostButton(self, "Close ForensiDrive", command=self.app.root.destroy).pack(anchor="w", pady=20)


class SystemInfoView(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        tk.Label(self, text="System information", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self, text="Simple facts about this session.", bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(4, 16))
        banner = Banner(self)
        body = ScrollBody(self)
        body.pack(fill="both", expand=True)

        try:
            info = collect_system_info()
        except AppError as exc:
            banner.show(exc.user_message, "error")
            details = TechnicalDetails(body.inner)
            details.pack(fill="x", pady=12)
            details.set_text(exc.combined_technical())
            return

        friendly = [
            ("ForensiDrive version", info["application_version"]),
            ("SystemRescue", info["systemrescue_version"]),
            ("Processor type", info["architecture"]),
            ("Memory available", info["memory"]),
            ("Startup mode", info["boot_mode"]),
        ]
        for label, value in friendly:
            row = tk.Frame(body.inner, bg=Theme.SURFACE)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, bg=Theme.SURFACE, fg=Theme.MUTED, font=(Theme.FONT, 12)).pack(anchor="w", padx=16, pady=(10, 0))
            tk.Label(row, text=value, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 15, "bold")).pack(anchor="w", padx=16, pady=(0, 10))

        details = TechnicalDetails(body.inner)
        details.pack(fill="x", pady=16)
        technical = "\n".join("%s: %s" % (key, value) for key, value in info.items())
        details.set_text(technical)
        PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=12)
