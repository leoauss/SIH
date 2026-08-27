import tkinter as tk
from tkinter import ttk

from core.errors import AppError, MissingCommandError, UserCancelledError
from core.filesystem import close_drive
from core.process import ProcessRunner
from integrations.erasure_tools import EraseMethod, build_command
from models.drive import Drive
from models.operation import Operation, OperationStatus
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, TechnicalDetails


class EraseProgressView(tk.Frame):
    def __init__(self, master, app, drive: Drive, method: EraseMethod):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.method = method
        self.runner = ProcessRunner()
        self.operation = Operation(kind="erasure", title=method.title)

        tk.Label(self, text="Erasing drive", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self, text="%s    %s    %s" % (drive.display_title(), drive.size_label, drive.path), bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(4, 12))
        self.banner = Banner(self)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", pady=8)
        self.cancel_btn = GhostButton(self, "Stop", command=self._cancel)
        self.cancel_btn.pack(anchor="w", pady=8)
        self.details = TechnicalDetails(self)
        self.details.pack(fill="both", expand=True, pady=8)
        self.after(100, self._begin)

    def _begin(self):
        try:
            notes = close_drive(self.drive)
            for note in notes:
                self.details.append_line(note)
        except AppError as exc:
            self.banner.show("Close the drive before continuing. " + exc.user_message, "error")
            self.details.set_text(exc.combined_technical())
            self.progress.pack_forget()
            PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w")
            return
        try:
            argv = build_command(self.method, self.drive)
        except Exception as exc:
            self.banner.show("We couldn't start the erase operation.", "error")
            self.details.set_text(str(exc))
            return
        self.banner.show("The erase operation is running. Do not unplug the drive.", "warn")
        self.progress.start(12)
        try:
            self.runner.start(argv, self.operation, on_line=self._on_line, on_done=self._on_done)
        except MissingCommandError as exc:
            self.progress.stop()
            self.banner.show(exc.user_message, "error")
            self.details.set_text(exc.combined_technical())

    def _on_line(self, line: str):
        self.after(0, lambda: self.details.append_line(line))

    def _on_done(self, operation: Operation):
        self.after(0, lambda: self._finished(operation))

    def _cancel(self):
        try:
            self.runner.cancel()
        except UserCancelledError:
            pass

    def _finished(self, operation: Operation):
        self.progress.stop()
        self.progress.pack_forget()
        self.cancel_btn.pack_forget()
        if operation.status == OperationStatus.SUCCEEDED:
            self.banner.show(
                "The operation completed successfully. ForensiDrive does not claim that the data is impossible to recover.",
                "ok",
            )
        elif operation.status == OperationStatus.CANCELLED:
            self.banner.show("The operation was cancelled.", "warn")
        else:
            self.banner.show(operation.user_message or "We couldn't complete this operation.", "error")
        PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=12)
