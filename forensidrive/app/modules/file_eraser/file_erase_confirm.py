import tkinter as tk
from typing import List

from integrations.file_erase_tools import FileEraseMethod
from models.drive import Drive
from models.file_target import FileTarget
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody


class FileEraseConfirmView(tk.Frame):
    """Safety gate before batch file erasure: two checkboxes required."""

    def __init__(self, master, app, drive: Drive,
                 targets: List[FileTarget], method: FileEraseMethod):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.targets = targets
        self.method = method
        self.understood = tk.BooleanVar(value=False)
        self.correct = tk.BooleanVar(value=False)

        tk.Label(self, text="Confirm permanent deletion",
                 bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(
            self,
            text="These files will be permanently deleted. This cannot be undone.",
            bg=Theme.BG, fg=Theme.ACCENT_DANGER, wraplength=900, justify="left",
        ).pack(anchor="w", pady=(8, 12))

        body = ScrollBody(self)
        body.pack(fill="both", expand=True)

        # File list card
        list_card = tk.Frame(body.inner, bg=Theme.SURFACE)
        list_card.pack(fill="x", pady=8)
        tk.Label(list_card, text="Files and folders to be erased (%d items):" % len(targets),
                 bg=Theme.SURFACE, fg=Theme.MUTED).pack(anchor="w", padx=16, pady=(10, 4))
        for t in targets:
            tk.Label(list_card,
                     text="%s  %s  (%s)" % (t.kind_label(), t.display_path(), t.size_label),
                     bg=Theme.SURFACE, fg=Theme.TEXT,
                     font=(Theme.FONT, 12), anchor="w").pack(fill="x", padx=24, pady=1)
        tk.Label(list_card, text="", bg=Theme.SURFACE).pack(pady=4)

        # Method card
        method_card = tk.Frame(body.inner, bg=Theme.SURFACE)
        method_card.pack(fill="x", pady=8)
        tk.Label(method_card, text="Erase method: %s" % method.title,
                 bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 14, "bold")).pack(
            anchor="w", padx=16, pady=(10, 2))
        tk.Label(method_card, text=method.warning, bg=Theme.SURFACE, fg=Theme.MUTED,
                 wraplength=800, justify="left").pack(anchor="w", padx=16, pady=(0, 10))

        # Checkboxes
        tk.Checkbutton(body.inner,
                       text="I understand these files will be permanently deleted.",
                       variable=self.understood,
                       bg=Theme.BG, fg=Theme.TEXT, selectcolor=Theme.SURFACE,
                       activebackground=Theme.BG, command=self._refresh).pack(anchor="w", pady=(16, 4))
        tk.Checkbutton(body.inner,
                       text="I have checked the list and confirmed these are the correct files.",
                       variable=self.correct,
                       bg=Theme.BG, fg=Theme.TEXT, selectcolor=Theme.SURFACE,
                       activebackground=Theme.BG, command=self._refresh).pack(anchor="w", pady=4)

        self.go_btn = PrimaryButton(self, "Delete selected files permanently",
                                    command=self._go, danger=True)
        self.go_btn.pack(anchor="w", pady=12)
        GhostButton(self, "Cancel", command=self.app.show_dashboard).pack(anchor="w")
        self._refresh()

    def _refresh(self):
        ready = self.understood.get() and self.correct.get()
        self.go_btn.configure(state="normal" if ready else "disabled")

    def _go(self):
        for child in self.winfo_children():
            child.destroy()
        from modules.file_eraser.file_erase_progress import FileEraseProgressView
        FileEraseProgressView(self, self.app, self.drive, self.targets, self.method).pack(
            fill="both", expand=True)
