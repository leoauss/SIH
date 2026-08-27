import tkinter as tk

from integrations.erasure_tools import EraseMethod
from models.drive import Drive
from modules.erasure.erase_progress import EraseProgressView
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody


class ConfirmationView(tk.Frame):
    def __init__(self, master, app, drive: Drive, method: EraseMethod):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.method = method
        self.understood = tk.BooleanVar(value=False)
        self.correct = tk.BooleanVar(value=False)
        self.typed = tk.StringVar(value="")

        tk.Label(self, text="Confirm the exact drive", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(
            self,
            text="This operation can permanently remove data. Check the drive name, size, and path twice.",
            bg=Theme.BG,
            fg=Theme.ACCENT_DANGER,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(8, 12))

        body = ScrollBody(self)
        body.pack(fill="both", expand=True)

        for heading in ("Selected drive", "Check this drive again"):
            box = tk.Frame(body.inner, bg=Theme.SURFACE)
            box.pack(fill="x", pady=8)
            tk.Label(box, text=heading, bg=Theme.SURFACE, fg=Theme.MUTED).pack(anchor="w", padx=16, pady=(10, 0))
            for line in drive.identity_lines():
                tk.Label(box, text=line, bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 14, "bold")).pack(anchor="w", padx=16)
            tk.Label(box, text=drive.friendly_kind(), bg=Theme.SURFACE, fg=Theme.MUTED).pack(anchor="w", padx=16, pady=(0, 10))

        tk.Label(body.inner, text="Erase method: %s" % method.title, bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 14, "bold")).pack(anchor="w", pady=(8, 4))
        tk.Label(body.inner, text=method.warning, bg=Theme.BG, fg=Theme.MUTED, wraplength=800, justify="left").pack(anchor="w")

        tk.Checkbutton(
            body.inner,
            text="I understand this can permanently remove data.",
            variable=self.understood,
            bg=Theme.BG,
            fg=Theme.TEXT,
            selectcolor=Theme.SURFACE,
            activebackground=Theme.BG,
            command=self._refresh,
        ).pack(anchor="w", pady=(16, 4))
        tk.Checkbutton(
            body.inner,
            text="I selected the correct drive.",
            variable=self.correct,
            bg=Theme.BG,
            fg=Theme.TEXT,
            selectcolor=Theme.SURFACE,
            activebackground=Theme.BG,
            command=self._refresh,
        ).pack(anchor="w", pady=4)

        tk.Label(body.inner, text="Type the drive path to confirm: %s" % drive.path, bg=Theme.BG, fg=Theme.TEXT).pack(anchor="w", pady=(12, 4))
        entry = tk.Entry(body.inner, textvariable=self.typed, bg=Theme.SURFACE_ALT, fg=Theme.TEXT, insertbackground=Theme.TEXT, font=(Theme.FONT, 13))
        entry.pack(fill="x", pady=4)
        self.typed.trace_add("write", lambda *_: self._refresh())

        self.go = PrimaryButton(self, "Erase this drive", command=self._go, danger=True)
        self.go.pack(anchor="w", pady=12)
        GhostButton(self, "Cancel", command=self.app.show_dashboard).pack(anchor="w")
        self._refresh()

    def _refresh(self):
        ready = (
            self.understood.get()
            and self.correct.get()
            and self.typed.get().strip() == self.drive.path
        )
        self.go.configure(state="normal" if ready else "disabled")

    def _go(self):
        for child in self.winfo_children():
            child.destroy()
        EraseProgressView(self, self.app, self.drive, self.method).pack(fill="both", expand=True)
