import os
import threading
import tkinter as tk
from tkinter import ttk
from typing import List

from core.audit import log_event
from core.errors import UserCancelledError
from core.process import ProcessRunner
from integrations.file_erase_tools import FileEraseMethod, build_file_command, build_folder_command
from integrations.metadata_tools import strip_metadata, sync_and_flush
from models.audit_event import AuditEvent
from models.drive import Drive
from models.file_target import FileTarget
from models.operation import Operation, OperationStatus
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, TechnicalDetails


class FileEraseProgressView(tk.Frame):
    """Processes each FileTarget sequentially: strip metadata -> overwrite -> delete."""

    def __init__(self, master, app, drive: Drive,
                 targets: List[FileTarget], method: FileEraseMethod):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.targets = list(targets)
        self.method = method
        self._cancelled = False
        self._current_index = 0
        self._succeeded = 0
        self._failed = 0

        tk.Label(self, text="Erasing files", bg=Theme.BG, fg=Theme.TEXT,
                 font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        self.stage_var = tk.StringVar(value="Starting...")
        tk.Label(self, textvariable=self.stage_var, bg=Theme.BG, fg=Theme.ACCENT,
                 font=(Theme.FONT, 12, "bold")).pack(anchor="w", pady=(4, 4))

        self.banner = Banner(self)

        self.overall_progress = ttk.Progressbar(self, mode="determinate",
                                                 maximum=len(targets), value=0)
        self.overall_progress.pack(fill="x", pady=4)

        self.file_progress = ttk.Progressbar(self, mode="indeterminate")
        self.file_progress.pack(fill="x", pady=2)
        self.file_progress.start(10)

        self.cancel_btn = GhostButton(self, "Stop", command=self._cancel)
        self.cancel_btn.pack(anchor="w", pady=8)

        self.details = TechnicalDetails(self)
        self.details.pack(fill="both", expand=True, pady=8)

        self.after(100, self._process_next)

    def _process_next(self):
        if self._cancelled or self._current_index >= len(self.targets):
            self._finish()
            return
        target = self.targets[self._current_index]
        total = len(self.targets)
        self.stage_var.set("Item %d of %d: %s" % (
            self._current_index + 1, total, target.display_name()))
        self.overall_progress.configure(value=self._current_index)

        def worker():
            ok = self._erase_target(target)
            if ok:
                self._succeeded += 1
            else:
                self._failed += 1
            self._current_index += 1
            self.after(0, self._process_next)

        threading.Thread(target=worker, daemon=True, name="forensidrive-file-erase").start()

    def _erase_target(self, target: FileTarget) -> bool:
        self._log("Processing: %s" % target.path)

        # Step A: strip metadata (files only)
        if not target.is_dir:
            result = strip_metadata(target.path)
            self._log("Metadata strip: %s" % ("ok" if result.ok else result.stderr[:120]))

        # Step B: overwrite
        if target.is_dir:
            argv = build_folder_command(self.method, target.path)
        else:
            argv = build_file_command(self.method, target.path)

        if argv:
            # Use ProcessRunner for real tool
            op = Operation(kind="file_erase", title=target.display_name(),
                           source_path=target.path)
            runner = ProcessRunner()
            done_event = threading.Event()
            _result_holder = []

            def on_done(operation):
                _result_holder.append(operation)
                done_event.set()

            try:
                runner.start(argv, op, on_done=on_done)
            except Exception as exc:
                self._log("Error: %s" % exc)
                return False
            done_event.wait(timeout=600)
            if _result_holder:
                erase_op = _result_holder[0]
                ok = erase_op.status == OperationStatus.SUCCEEDED
                self._log("Erase result: %s" % erase_op.status.value)
                return ok
            return False
        else:
            # Python zero fallback
            return self._python_zero(target)

    def _python_zero(self, target: FileTarget) -> bool:
        try:
            paths = []
            if target.is_dir:
                for dirpath, _, filenames in os.walk(target.path):
                    for fn in filenames:
                        paths.append(os.path.join(dirpath, fn))
            else:
                paths = [target.path]
            for p in paths:
                size = os.path.getsize(p)
                with open(p, "r+b") as fh:
                    fh.write(b"\x00" * size)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.unlink(p)
                self._log("Zeroed and deleted: %s" % p)
            if target.is_dir:
                import shutil
                shutil.rmtree(target.path, ignore_errors=True)
            return True
        except OSError as exc:
            self._log("Error (python fallback): %s" % exc)
            return False

    def _finish(self):
        self.file_progress.stop()
        self.file_progress.pack_forget()
        self.cancel_btn.pack_forget()
        self.overall_progress.configure(value=len(self.targets))

        # Flush disk
        sync_and_flush()

        # Audit log
        event = AuditEvent(
            kind="file_erase",
            drive_path=self.drive.path,
            serial=self.drive.serial,
            method_id=self.method.id,
            method_title=self.method.title,
            status="cancelled" if self._cancelled else ("succeeded" if self._failed == 0 else "partial"),
            files_erased=self._succeeded,
            files_failed=self._failed,
        )
        log_event(event)

        if self._cancelled:
            self.banner.show("Operation stopped. %d erased, %d failed." % (
                self._succeeded, self._failed), "warn")
        elif self._failed == 0:
            self.banner.show(
                "%d item(s) erased successfully. Audit record written." % self._succeeded, "ok")
        else:
            self.banner.show(
                "%d erased, %d failed. Review technical details." % (
                    self._succeeded, self._failed), "warn")

        PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=12)

    def _log(self, text: str):
        self.after(0, lambda t=text: self.details.append_line(t))

    def _cancel(self):
        self._cancelled = True
        self.stage_var.set("Stopping after current file...")
