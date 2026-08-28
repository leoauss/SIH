import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import List

from core.storage import format_size
from integrations.file_erase_tools import FileEraseMethod, list_file_methods
from models.drive import Drive
from models.file_target import FileTarget
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, ScrollBody


class FileTargetView(tk.Frame):
    """File browser and method selector: pick files/folders then continue."""

    def __init__(self, master, app, drive: Drive):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self._targets: List[FileTarget] = []

        tk.Label(self, text="Choose files to erase permanently",
                 bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self, text="Drive: %s (%s)" % (drive.display_title(), drive.path),
                 bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(4, 12))

        # ---- Toolbar ----
        toolbar = tk.Frame(self, bg=Theme.BG)
        toolbar.pack(fill="x", pady=(0, 8))
        GhostButton(toolbar, "Add files", command=self._add_files).pack(side="left", padx=(0, 8))
        GhostButton(toolbar, "Add folder", command=self._add_folder).pack(side="left", padx=(0, 8))
        GhostButton(toolbar, "Remove selected", command=self._remove_selected).pack(side="left")

        # ---- File list ----
        list_frame = tk.Frame(self, bg=Theme.SURFACE)
        list_frame.pack(fill="both", expand=True, pady=(0, 8))

        cols = ("kind", "name", "size", "path")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="extended",
                                 height=12)
        self.tree.heading("kind", text="Type")
        self.tree.heading("name", text="Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("path", text="Full path")
        self.tree.column("kind", width=60, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("size", width=90, anchor="e")
        self.tree.column("path", width=500)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ---- Method selector ----
        method_row = tk.Frame(self, bg=Theme.SURFACE)
        method_row.pack(fill="x", pady=4)
        tk.Label(method_row, text="Erase method:", bg=Theme.SURFACE,
                 fg=Theme.MUTED).pack(side="left", padx=12, pady=10)
        self._method_var = tk.StringVar()
        methods = list_file_methods()
        usable = [m for m in methods if m.available]
        self._methods_map = {m.title: m for m in methods}
        choices = [m.title for m in (usable if usable else methods)]
        if choices:
            self._method_var.set(choices[0])
        opt = tk.OptionMenu(method_row, self._method_var, *choices)
        opt.configure(bg=Theme.SURFACE_ALT, fg=Theme.TEXT, highlightthickness=0,
                      relief="flat", font=(Theme.FONT, Theme.FONT_SIZE))
        opt.pack(side="left", padx=8)

        # ---- Footer ----
        self.footer_var = tk.StringVar(value="No files selected.")
        tk.Label(self, textvariable=self.footer_var, bg=Theme.BG,
                 fg=Theme.MUTED, font=(Theme.FONT, 11)).pack(anchor="w", pady=4)

        btn_row = tk.Frame(self, bg=Theme.BG)
        btn_row.pack(fill="x", pady=4)
        PrimaryButton(btn_row, "Review and confirm", command=self._review,
                      danger=True).pack(side="left")
        GhostButton(btn_row, "Back", command=self.app.show_file_eraser).pack(side="left", padx=12)

    # ------------------------------------------------------------------

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select files to erase",
            initialdir=self._initial_dir(),
        )
        for path in paths:
            self._add_path(path, is_dir=False)
        self._refresh_footer()

    def _add_folder(self):
        path = filedialog.askdirectory(
            title="Select a folder to erase",
            initialdir=self._initial_dir(),
        )
        if path:
            self._add_path(path, is_dir=True)
        self._refresh_footer()

    def _initial_dir(self) -> str:
        # Start in the drive's first mounted partition, if any
        for part in self.drive.partitions:
            if part.mountpoint:
                return part.mountpoint
        return "/"

    def _add_path(self, path: str, is_dir: bool):
        # Don't add duplicates
        if any(t.path == path for t in self._targets):
            return
        try:
            size = _dir_size(path) if is_dir else os.path.getsize(path)
        except OSError:
            size = 0
        target = FileTarget(path=path, size_bytes=size,
                            size_label=format_size(size), is_dir=is_dir)
        self._targets.append(target)
        self.tree.insert("", "end",
                         values=(target.kind_label(), target.display_name(),
                                 target.size_label, target.path))

    def _remove_selected(self):
        selected = self.tree.selection()
        for iid in selected:
            values = self.tree.item(iid, "values")
            path = values[3] if len(values) > 3 else ""
            self._targets = [t for t in self._targets if t.path != path]
            self.tree.delete(iid)
        self._refresh_footer()

    def _refresh_footer(self):
        count = len(self._targets)
        total = sum(t.size_bytes for t in self._targets)
        if count == 0:
            self.footer_var.set("No files selected.")
        else:
            self.footer_var.set("%d item(s) selected — %s total" % (count, format_size(total)))

    def _review(self):
        if not self._targets:
            return
        chosen_title = self._method_var.get()
        method = self._methods_map.get(chosen_title)
        if method is None:
            return
        for child in self.winfo_children():
            child.destroy()
        from modules.file_eraser.file_erase_confirm import FileEraseConfirmView
        FileEraseConfirmView(self, self.app, self.drive, self._targets, method).pack(
            fill="both", expand=True)


def _dir_size(path: str) -> int:
    total = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for fn in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, fn))
                except OSError:
                    pass
    except OSError:
        pass
    return total
