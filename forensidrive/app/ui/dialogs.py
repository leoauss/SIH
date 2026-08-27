"""Simple dialogs with user-friendly wording."""

import tkinter as tk
from tkinter import filedialog, messagebox


def ask_folder(parent, title="Choose a folder") -> str:
    return filedialog.askdirectory(parent=parent, title=title) or ""


def show_error(parent, message: str, technical: str = "") -> None:
    extra = ""
    if technical:
        extra = "\n\nTechnical details are available in the main window."
    messagebox.showerror("Something went wrong", message + extra, parent=parent)


def show_info(parent, message: str) -> None:
    messagebox.showinfo("ForensiDrive", message, parent=parent)


def confirm(parent, title: str, message: str) -> bool:
    return messagebox.askyesno(title, message, parent=parent)
