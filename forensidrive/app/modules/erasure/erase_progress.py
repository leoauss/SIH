import threading
import tkinter as tk
from tkinter import ttk

from core.audit import log_event
from core.errors import AppError, MissingCommandError, UserCancelledError
from core.filesystem import close_drive
from core.hashing import format_hash, hash_device
from core.process import ProcessRunner
from integrations.erasure_tools import EraseMethod, build_command
from integrations.verify_tools import verify_zeros
from models.audit_event import AuditEvent
from models.drive import Drive
from models.operation import Operation, OperationStatus
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, TechnicalDetails


class EraseProgressView(tk.Frame):
    """
    4-step erase flow:
      Step 1 — Fingerprint (SHA-256 before)
      Step 2 — Erase (tool subprocess)
      Step 3 — Verify (read-back zero check)
      Step 4 — Audit log write
    """

    def __init__(self, master, app, drive: Drive, method: EraseMethod):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.method = method
        self.runner = ProcessRunner()
        self.operation = Operation(
            kind="erasure",
            title=method.title,
            source_path=drive.path,
            standard_id=method.standard_id,
        )

        tk.Label(self, text="Erasing drive", bg=Theme.BG, fg=Theme.TEXT,
                 font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(self,
                 text="%s    %s    %s" % (drive.display_title(), drive.size_label, drive.path),
                 bg=Theme.BG, fg=Theme.MUTED).pack(anchor="w", pady=(4, 12))

        self.banner = Banner(self)

        # Stage indicator
        self.stage_var = tk.StringVar(value="Preparing...")
        tk.Label(self, textvariable=self.stage_var, bg=Theme.BG, fg=Theme.ACCENT,
                 font=(Theme.FONT, 12, "bold")).pack(anchor="w", pady=(0, 4))

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", pady=4)

        self.cancel_btn = GhostButton(self, "Stop", command=self._cancel)
        self.cancel_btn.pack(anchor="w", pady=8)

        self.details = TechnicalDetails(self)
        self.details.pack(fill="both", expand=True, pady=8)

        self.after(100, self._step1_fingerprint)

    # ------------------------------------------------------------------
    # Step 1 — SHA-256 before erase
    # ------------------------------------------------------------------
    def _step1_fingerprint(self):
        self._set_stage("Step 1 of 4: Fingerprinting drive before erase...")
        self.progress.start(12)

        def worker():
            digest = hash_device(
                self.drive.path,
                on_progress=lambda msg: self.after(0, lambda m=msg: self.details.append_line(m)),
            )
            self.after(0, lambda: self._step1_done(digest))

        threading.Thread(target=worker, daemon=True, name="forensidrive-hash-before").start()

    def _step1_done(self, digest: str):
        self.operation.hash_before = digest
        self.details.append_line("SHA-256 before: %s" % (digest or "unavailable"))
        self._step2_close_and_erase()

    # ------------------------------------------------------------------
    # Step 2 — Unmount + erase
    # ------------------------------------------------------------------
    def _step2_close_and_erase(self):
        self._set_stage("Step 2 of 4: Erasing drive...")
        # Unmount first
        try:
            notes = close_drive(self.drive)
            for note in notes:
                self.details.append_line(note)
        except AppError as exc:
            self.progress.stop()
            self.banner.show("Close the drive before continuing. " + exc.user_message, "error")
            self.details.set_text(exc.combined_technical())
            PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w")
            return

        try:
            argv = build_command(self.method, self.drive)
        except Exception as exc:
            self.progress.stop()
            self.banner.show("We couldn't start the erase operation.", "error")
            self.details.set_text(str(exc))
            return

        self.banner.show("The erase operation is running. Do not unplug the drive.", "warn")
        try:
            self.runner.start(argv, self.operation,
                              on_line=self._on_line,
                              on_done=self._step2_done)
        except MissingCommandError as exc:
            self.progress.stop()
            self.banner.show(exc.user_message, "error")
            self.details.set_text(exc.combined_technical())

    def _on_line(self, line: str):
        self.after(0, lambda: self.details.append_line(line))

    def _step2_done(self, operation: Operation):
        self.after(0, lambda: self._step3_verify(operation))

    # ------------------------------------------------------------------
    # Step 3 — Verification read-back
    # ------------------------------------------------------------------
    def _step3_verify(self, operation: Operation):
        if operation.status == OperationStatus.CANCELLED:
            self._finish(operation, verify_passed=None)
            return

        self._set_stage("Step 3 of 4: Verifying erasure...")

        def worker():
            result = verify_zeros(self.drive.path)
            self.after(0, lambda: self._step3_done(operation, result))

        threading.Thread(target=worker, daemon=True, name="forensidrive-verify").start()

    def _step3_done(self, operation, verify_result):
        self.details.append_line(verify_result.technical)
        self._step4_audit(operation, verify_result.passed)

    # ------------------------------------------------------------------
    # Step 4 — Write audit log
    # ------------------------------------------------------------------
    def _step4_audit(self, operation: Operation, verify_passed):
        self._set_stage("Step 4 of 4: Writing audit record...")
        event = AuditEvent(
            kind="erasure",
            drive_path=self.drive.path,
            serial=self.drive.serial,
            method_id=self.method.id,
            method_title=self.method.title,
            standard_id=self.method.standard_id,
            status=operation.status.value,
            user_message=operation.user_message,
            hash_before=operation.hash_before or "",
            notes="Verify pass: %s" % ("PASS" if verify_passed else ("FAIL" if verify_passed is False else "skipped")),
            technical_lines=operation.technical_lines,
        )
        log_event(event)
        self.details.append_line("Audit record written: %s" % event.id)
        self._finish(operation, verify_passed)

    # ------------------------------------------------------------------
    # Final display
    # ------------------------------------------------------------------
    def _finish(self, operation: Operation, verify_passed):
        self.progress.stop()
        self.progress.pack_forget()
        self.cancel_btn.pack_forget()

        if operation.status == OperationStatus.CANCELLED:
            self.banner.show("The operation was cancelled.", "warn")
        elif operation.status == OperationStatus.SUCCEEDED:
            if verify_passed is True:
                msg = (
                    "The erase operation completed and the verification pass found no data. "
                    "ForensiDrive does not claim that the data is impossible to recover."
                )
                self.banner.show(msg, "ok")
            elif verify_passed is False:
                self.banner.show(
                    "The erase tool reported success but the verification pass found non-zero data. "
                    "Review the technical details.", "warn")
            else:
                self.banner.show(
                    "The operation completed. ForensiDrive does not claim that the data is impossible to recover.",
                    "ok")
        else:
            self.banner.show(operation.user_message or "We couldn't complete this operation.", "error")

        # Show hash summary
        if operation.hash_before:
            tk.Label(self, text="Drive fingerprint (SHA-256 before erase):",
                     bg=Theme.BG, fg=Theme.MUTED, font=(Theme.FONT, 10)).pack(anchor="w", pady=(8, 0))
            tk.Label(self, text=format_hash(operation.hash_before),
                     bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 11, "bold")).pack(anchor="w")

        PrimaryButton(self, "Back to Home", command=self.app.show_dashboard).pack(anchor="w", pady=12)

    def _set_stage(self, text: str):
        self.stage_var.set(text)

    def _cancel(self):
        try:
            self.runner.cancel()
        except UserCancelledError:
            pass
