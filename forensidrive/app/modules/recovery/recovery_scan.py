import threading
import tkinter as tk
from tkinter import ttk

from core.audit import log_event
from core.classifier import ClassificationReport, classify_directory
from core.errors import MissingCommandError, UserCancelledError
from core.evidence import create_case_id, hash_destination_tree, hash_source, write_chain_of_custody
from core.process import ProcessRunner
from integrations.recovery_tools import RecoveryMethod, build_command
from models.audit_event import AuditEvent
from models.drive import Drive
from models.operation import Operation, OperationStatus
from modules.recovery.recovery_results import RecoveryResultsView
from ui.dialogs import ask_folder, show_error
from ui.notifications import Banner
from ui.theme import Theme
from ui.widgets import GhostButton, PrimaryButton, TechnicalDetails


class RecoveryScanView(tk.Frame):
    """
    Enhanced 4-step recovery pipeline:
      Step 1 — Source Fingerprinting (SHA-256)
      Step 2 — File Carving & Recovery (ProcessRunner)
      Step 3 — Post-Recovery File Classification & Confidence Scoring
      Step 4 — Chain of Custody & Audit Logging
    """

    def __init__(self, master, app, drive: Drive, method: RecoveryMethod):
        super().__init__(master, bg=Theme.BG)
        self.app = app
        self.drive = drive
        self.method = method
        self.destination = tk.StringVar(value="")
        self.runner = ProcessRunner()
        self.operation = Operation(
            kind="recovery",
            title=self.method.title,
            source_path=drive.path,
        )
        self.case_id = create_case_id()
        self.classification_report = None
        self.chain_of_custody_path = None

        tk.Label(self, text="File Recovery & Carving", bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 22, "bold")).pack(anchor="w")
        tk.Label(
            self,
            text="Save recovered files to a safe destination drive, not the drive being examined.",
            bg=Theme.BG,
            fg=Theme.MUTED,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(4, 12))
        self.banner = Banner(self)

        dest_row = tk.Frame(self, bg=Theme.SURFACE)
        dest_row.pack(fill="x", pady=8)
        tk.Label(dest_row, textvariable=self.destination, bg=Theme.SURFACE, fg=Theme.TEXT, wraplength=700, justify="left").pack(anchor="w", padx=16, pady=12)
        GhostButton(dest_row, "Choose output folder", command=self._pick).pack(anchor="w", padx=16, pady=(0, 12))

        # Stage label
        self.stage_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.stage_var, bg=Theme.BG, fg=Theme.ACCENT, font=(Theme.FONT, 12, "bold")).pack(anchor="w", pady=(8, 4))

        self.start_btn = PrimaryButton(self, "Start recovery", command=self._start)
        self.start_btn.pack(anchor="w", pady=4)
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

        self.operation.destination = dest
        self.start_btn.pack_forget()
        self.cancel_btn.pack(anchor="w", pady=4)
        self.progress.pack(fill="x", pady=8)
        self.progress.start(12)

        self._step1_fingerprint(dest)

    # ------------------------------------------------------------------
    # Step 1: Fingerprint source drive
    # ------------------------------------------------------------------
    def _step1_fingerprint(self, dest: str):
        self.stage_var.set("Step 1 of 4: Fingerprinting source drive (SHA-256)...")
        self.banner.show("Establishing forensic hash of the source drive...", "info")

        def worker():
            digest = hash_source(
                self.drive.path,
                on_progress=lambda msg: self.after(0, lambda m=msg: self.details.append_line(m)),
            )
            self.after(0, lambda: self._step1_done(digest, dest))

        threading.Thread(target=worker, daemon=True, name="forensidrive-rec-hash").start()

    def _step1_done(self, digest: str, dest: str):
        self.operation.hash_before = digest
        self.details.append_line("Source SHA-256 digest: %s" % (digest or "unavailable"))
        self._step2_carve(dest)

    # ------------------------------------------------------------------
    # Step 2: Carve / Recover files
    # ------------------------------------------------------------------
    def _step2_carve(self, dest: str):
        self.stage_var.set("Step 2 of 4: Searching and carving files...")
        self.banner.show("Carving files from storage media. This may take some time.", "info")

        try:
            argv = build_command(self.method, self.drive, dest)
        except Exception as exc:
            self._finish_failed("We couldn't start recovery.", str(exc))
            return

        try:
            self.runner.start(argv, self.operation, on_line=self._on_line, on_done=lambda op: self._step3_classify(op, dest))
        except MissingCommandError as exc:
            self._finish_failed(exc.user_message, exc.combined_technical())

    def _on_line(self, line: str):
        self.after(0, lambda: self.details.append_line(line))

    # ------------------------------------------------------------------
    # Step 3: Classify recovered files
    # ------------------------------------------------------------------
    def _step3_classify(self, operation: Operation, dest: str):
        if operation.status == OperationStatus.CANCELLED:
            self._step4_audit_and_finish(operation, dest)
            return

        self.stage_var.set("Step 3 of 4: Classifying recovered files & calculating confidence...")
        self.banner.show("Analyzing file magic headers and integrity...", "info")

        def worker():
            report = classify_directory(dest)
            dest_hashes = hash_destination_tree(dest)
            coc_path = write_chain_of_custody(
                case_id=self.case_id,
                source_path=self.drive.path,
                source_hash=operation.hash_before or "",
                dest_hashes=dest_hashes,
                folder=dest,
                tool_used=self.method.title,
            )
            self.after(0, lambda: self._step3_done(operation, report, coc_path, dest))

        threading.Thread(target=worker, daemon=True, name="forensidrive-classify").start()

    def _step3_done(self, operation: Operation, report: ClassificationReport, coc_path, dest: str):
        self.classification_report = report
        self.chain_of_custody_path = str(coc_path)
        operation.add_technical("Classification complete: %d total files found." % report.total_files)
        operation.add_technical("Chain of custody generated: %s" % coc_path)
        self._step4_audit_and_finish(operation, dest)

    # ------------------------------------------------------------------
    # Step 4: Audit Logging & Navigation
    # ------------------------------------------------------------------
    def _step4_audit_and_finish(self, operation: Operation, dest: str):
        self.stage_var.set("Step 4 of 4: Recording audit log...")
        file_count = self.classification_report.total_files if self.classification_report else 0

        event = AuditEvent(
            id=self.case_id,
            kind="recovery",
            drive_path=self.drive.path,
            serial=self.drive.serial,
            method_id=self.method.id,
            method_title=self.method.title,
            status=operation.status.value,
            user_message=operation.user_message,
            hash_before=operation.hash_before or "",
            destination=dest,
            files_recovered=file_count,
            notes="Chain of custody: %s" % (self.chain_of_custody_path or "n/a"),
            technical_lines=operation.technical_lines,
        )
        log_event(event)

        self._show_result(operation)

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
        RecoveryResultsView(
            self,
            self.app,
            self.drive,
            self.method,
            operation,
            self.destination.get(),
            self.classification_report,
            self.chain_of_custody_path,
        ).pack(fill="both", expand=True)
