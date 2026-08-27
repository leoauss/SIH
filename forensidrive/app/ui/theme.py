"""Visual theme for a simple, high-contrast primary interface."""

import tkinter as tk
from tkinter import ttk


class Theme:
    BG = "#101418"
    SURFACE = "#1b222b"
    SURFACE_ALT = "#24303c"
    ACCENT = "#3d8bfd"
    ACCENT_DANGER = "#d64545"
    ACCENT_OK = "#2f9e62"
    TEXT = "#f4f7fb"
    MUTED = "#a8b3c1"
    BORDER = "#334155"
    FONT = "TkDefaultFont"
    FONT_SIZE = 13
    TITLE_SIZE = 22
    BUTTON_SIZE = 15


def apply(root: tk.Tk) -> None:
    root.configure(bg=Theme.BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TFrame", background=Theme.BG)
    style.configure("Card.TFrame", background=Theme.SURFACE)
    style.configure("TLabel", background=Theme.BG, foreground=Theme.TEXT, font=(Theme.FONT, Theme.FONT_SIZE))
    style.configure("Muted.TLabel", background=Theme.BG, foreground=Theme.MUTED, font=(Theme.FONT, Theme.FONT_SIZE))
    style.configure("Title.TLabel", background=Theme.BG, foreground=Theme.TEXT, font=(Theme.FONT, Theme.TITLE_SIZE, "bold"))
    style.configure("Card.TLabel", background=Theme.SURFACE, foreground=Theme.TEXT, font=(Theme.FONT, Theme.FONT_SIZE))
    style.configure("CardMuted.TLabel", background=Theme.SURFACE, foreground=Theme.MUTED, font=(Theme.FONT, Theme.FONT_SIZE))
    style.configure("CardTitle.TLabel", background=Theme.SURFACE, foreground=Theme.TEXT, font=(Theme.FONT, 16, "bold"))
    style.configure("TButton", font=(Theme.FONT, Theme.BUTTON_SIZE), padding=10)
    style.configure("Accent.TButton", font=(Theme.FONT, Theme.BUTTON_SIZE, "bold"), padding=12)
    style.configure("Danger.TButton", font=(Theme.FONT, Theme.BUTTON_SIZE, "bold"), padding=12)
    style.configure("TCheckbutton", background=Theme.BG, foreground=Theme.TEXT, font=(Theme.FONT, Theme.FONT_SIZE))
    style.configure("TRadiobutton", background=Theme.BG, foreground=Theme.TEXT, font=(Theme.FONT, Theme.FONT_SIZE))
    style.configure("TEntry", fieldbackground=Theme.SURFACE_ALT, foreground=Theme.TEXT)
    style.configure("Horizontal.TProgressbar", background=Theme.ACCENT, troughcolor=Theme.SURFACE_ALT)
    style.map("Accent.TButton", background=[("active", Theme.ACCENT)])
    style.map("Danger.TButton", background=[("active", Theme.ACCENT_DANGER)])
