"""Reusable Tk widgets."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from models.drive import Drive
from ui.theme import Theme


class ScrollBody(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, bg=Theme.BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self._stretch)

        # Cross-platform mouse wheel scrolling (Linux X11 Button-4/5 + Windows/macOS MouseWheel)
        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)
        self.bind("<Destroy>", self._unbind_mousewheel)

    def _stretch(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)

    def _bind_mousewheel(self, _event=None):
        # Linux X11 mouse wheel events
        self.bind_all("<Button-4>", self._on_wheel_up)
        self.bind_all("<Button-5>", self._on_wheel_down)
        # Windows / macOS mouse wheel
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        try:
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass

    def _on_wheel_up(self, _event):
        self.canvas.yview_scroll(-2, "units")

    def _on_wheel_down(self, _event):
        self.canvas.yview_scroll(2, "units")

    def _on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(-int(event.delta / 60), "units")


class PrimaryButton(tk.Button):
    def __init__(self, master, text, command=None, danger=False, **kwargs):
        bg = Theme.ACCENT_DANGER if danger else Theme.ACCENT
        super().__init__(
            master,
            text=text,
            command=command,
            bg=bg,
            fg="#ffffff",
            activebackground=bg,
            activeforeground="#ffffff",
            relief="flat",
            font=(Theme.FONT, Theme.BUTTON_SIZE, "bold"),
            padx=18,
            pady=14,
            cursor="hand2",
            **kwargs
        )


class GhostButton(tk.Button):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            bg=Theme.SURFACE_ALT,
            fg=Theme.TEXT,
            activebackground=Theme.BORDER,
            activeforeground=Theme.TEXT,
            relief="flat",
            font=(Theme.FONT, Theme.FONT_SIZE),
            padx=14,
            pady=10,
            cursor="hand2",
            **kwargs
        )


class DriveCard(tk.Frame):
    def __init__(self, master, drive: Drive, on_select: Optional[Callable[[Drive], None]] = None, selected=False):
        super().__init__(master, bg=Theme.SURFACE, highlightthickness=2, highlightbackground=Theme.ACCENT if selected else Theme.BORDER)
        self.drive = drive
        title = tk.Label(self, text=drive.display_title(), bg=Theme.SURFACE, fg=Theme.TEXT, font=(Theme.FONT, 16, "bold"), anchor="w")
        title.pack(fill="x", padx=16, pady=(12, 2))
        subtitle = "%s    %s" % (drive.size_label, drive.path)
        tk.Label(self, text=subtitle, bg=Theme.SURFACE, fg=Theme.MUTED, font=(Theme.FONT, Theme.FONT_SIZE), anchor="w").pack(fill="x", padx=16)
        tk.Label(self, text=drive.friendly_kind(), bg=Theme.SURFACE, fg=Theme.MUTED, font=(Theme.FONT, 11), anchor="w").pack(fill="x", padx=16, pady=(0, 12))
        if on_select:
            for widget in (self, title):
                widget.bind("<Button-1>", lambda _e, d=drive: on_select(d))


class TechnicalDetails(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=Theme.BG)
        self._open = False
        self.toggle = GhostButton(self, "Technical details", command=self._toggle)
        self.toggle.pack(anchor="w")
        self.body = tk.Text(
            self,
            height=10,
            wrap="word",
            bg=Theme.SURFACE,
            fg=Theme.MUTED,
            insertbackground=Theme.TEXT,
            relief="flat",
            state="disabled",
        )

    def _toggle(self):
        self._open = not self._open
        if self._open:
            self.body.pack(fill="both", expand=True, pady=(8, 0))
        else:
            self.body.pack_forget()

    def set_text(self, text: str):
        self.body.configure(state="normal")
        self.body.delete("1.0", "end")
        self.body.insert("1.0", text or "No technical details.")
        self.body.configure(state="disabled")

    def append_line(self, line: str):
        self.body.configure(state="normal")
        self.body.insert("end", line + "\n")
        self.body.see("end")
        self.body.configure(state="disabled")
