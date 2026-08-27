"""In-window status banners. Avoid raw subprocess text here."""

import tkinter as tk

from ui.theme import Theme


class Banner(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=Theme.SURFACE_ALT)
        self.label = tk.Label(self, text="", bg=Theme.SURFACE_ALT, fg=Theme.TEXT, font=(Theme.FONT, 13), wraplength=900, justify="left")
        self.label.pack(fill="x", padx=16, pady=10)
        self.pack_forget()

    def show(self, message: str, kind="info"):
        colors = {
            "info": (Theme.SURFACE_ALT, Theme.TEXT),
            "ok": ("#163527", Theme.TEXT),
            "error": ("#3a1515", Theme.TEXT),
            "warn": ("#3a2a10", Theme.TEXT),
        }
        bg, fg = colors.get(kind, colors["info"])
        self.configure(bg=bg)
        self.label.configure(text=message, bg=bg, fg=fg)
        self.pack(fill="x", pady=(0, 12))

    def clear(self):
        self.pack_forget()
