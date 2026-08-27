import tkinter as tk
from tkinter import ttk

from core.errors import AppError, MissingCommandError, UserCancelledError
from core.process import ProcessRunner
from integrations.recovery_tools import RecoveryMethod, build_command
from models.drive import Drive
from models.operation import Operation
from modules.recovery.recovery_results import RecoveryResultsView
from ui.dialogs import ask_folder, show_error
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, TechnicalDetails


class RecoveryScanView(tk.Frame):
    def __init__(self, master, app, drive: Drive, method: RecoveryMethod):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.method = method
        self.destination = tk.StringVar(value="")
        self.runner = ProcessRunner()
        self.operation = None

        tk.Label(self, text="Choose where recovered files should be saved", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(
            self,
            text="Save them on a different drive when you can, not on the same drive you are searching.",
            bg=Theme.BG,
            fg=Theme.MUTED,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(4, 12))
        self.banner = Banner(self)

        dest_row = tk.Frame(self, bg=Theme.SURFACE)
        dest_row.pack(fill="x", pady=8)
        tk.Label(dest_row, textvariable=self.destination, bg=Theme.SURFACE, fg=Theme.TEXT, wraplength=700, justify="left").pack(anchor="w", padx=16, pady=12)
        GhostButton(dest_row, "Choose folder", command=self._pick).pack(anchor="w", padx=16, pady=(0, 12))

        self.start_btn = PrimaryButton(self, "Start recovery", command=self._start)
        self.start_btn.pack(anchor="w", pady=12)
        self.cancel_btn = GhostButton(self, "Stop", command=self._cancel)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.details = TechnicalDetails(self)
        self.details.pack(fill="both", expand=True, pady=8)
        GhostButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=8)

    def _pick(self):
        chosen = ask_folder(self, "Choose where recovered files should be saved")
        if chosen:
            self.destination.set(chosen)

    def _start(self):
        dest = self.destination.get().strip()
        if not dest:
            self.banner.show("Please choose where recovered files should be saved.", "warn")
            return
        try:
            argv = build_command(self.method, self.drive, dest)
        except Exception as exc:
            show_error(self, "We couldn't start recovery.", str(exc))
            return
        self.operation = Operation(kind="recovery", title=self.method.title)
        self.start_btn.pack_forget()
        self.cancel_btn.pack(anchor="w", pady=8)
        self.progress.pack(fill="x", pady=8)
        self.progress.start(12)
        self.banner.show("Looking for files. This can take a long time.", "info")
        try:
            self.runner.start(argv, self.operation, on_line=self._on_line, on_done=self._on_done)
        except MissingCommandError as exc:
            self._finish_failed(exc.user_message, exc.combined_technical())

    def _on_line(self, line: str):
        self.after(0, lambda: self.details.append_line(line))

    def _on_done(self, operation: Operation):
        self.after(0, lambda: self._show_result(operation))

    def _cancel(self):
        try:
            self.runner.cancel()
        except UserCancelledError:
            pass

    def _finish_failed(self, message, technical):
        self.progress.stop()
        self.progress.pack_forget()
        self.banner.show(message, "error")
        self.details.set_text(technical)

    def _show_result(self, operation: Operation):
        self.progress.stop()
        for child in self.winfo_children():
            child.destroy()
        RecoveryResultsView(self, self.app, self.drive, self.method, operation, self.destination.get()).pack(fill="both", expand=True)
