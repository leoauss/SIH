"""Long-running process runner used by recovery and erasure."""

import os
import signal
import subprocess
import threading
from typing import Callable, List, Optional, Sequence

from core.errors import MissingCommandError, UserCancelledError
from core.commands import resolve_executable
from models.operation import Operation, OperationStatus


LineCallback = Callable[[str], None]
DoneCallback = Callable[[Operation], None]


class ProcessRunner:
    def __init__(self):
        self._proc = None
        self._thread = None
        self._cancel = threading.Event()
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        with self._lock:
            return self._proc is not None and self._proc.poll() is None

    def start(
        self,
        argv: Sequence[str],
        operation: Operation,
        on_line: Optional[LineCallback] = None,
        on_done: Optional[DoneCallback] = None,
        cwd=None,
    ) -> None:
        executable = resolve_executable(str(argv[0]))
        if executable is None:
            operation.status = OperationStatus.FAILED
            operation.user_message = "This system does not have the tool needed for this step."
            operation.add_technical("Command not found: %s" % argv[0])
            raise MissingCommandError(operation.user_message, "Command not found: %s" % argv[0])

        self._cancel.clear()
        operation.status = OperationStatus.RUNNING
        operation.command = list(argv)
        operation.add_technical("Command: " + " ".join(argv))

        def worker():
            try:
                proc = subprocess.Popen(
                    list(argv),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cwd,
                    shell=False,
                    text=True,
                    errors="replace",
                    bufsize=1,
                )
            except OSError as exc:
                operation.status = OperationStatus.FAILED
                operation.user_message = "We couldn't start this operation."
                operation.add_technical(str(exc))
                if on_done:
                    on_done(operation)
                return

            with self._lock:
                self._proc = proc

            try:
                if proc.stdout is not None:
                    for line in proc.stdout:
                        line = line.rstrip("\n")
                        operation.add_technical(line)
                        if on_line:
                            on_line(line)
                        if self._cancel.is_set():
                            _terminate(proc)
                            break
                proc.wait()
            finally:
                with self._lock:
                    self._proc = None

            if self._cancel.is_set():
                operation.status = OperationStatus.CANCELLED
                operation.user_message = "The operation was cancelled."
                operation.return_code = proc.returncode
            elif proc.returncode == 0:
                operation.status = OperationStatus.SUCCEEDED
                operation.user_message = "The operation completed successfully."
                operation.return_code = 0
            else:
                operation.status = OperationStatus.FAILED
                operation.user_message = "We couldn't complete this operation."
                operation.return_code = proc.returncode
                operation.add_technical("Exit code: %s" % proc.returncode)

            if on_done:
                on_done(operation)

        self._thread = threading.Thread(target=worker, name="forensidrive-proc", daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        self._cancel.set()
        with self._lock:
            proc = self._proc
        if proc is not None:
            _terminate(proc)
            raise UserCancelledError("The operation was cancelled.", "")


def _terminate(proc: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except OSError:
                proc.terminate()
        else:
            proc.terminate()
    except OSError:
        pass
