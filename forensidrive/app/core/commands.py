"""Safe subprocess helpers. GUI code must not call subprocess directly."""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from core.errors import (
    AppError,
    CommandFailedError,
    CommandTimeoutError,
    MissingCommandError,
    PermissionDeniedError,
)


@dataclass
class CommandResult:
    argv: List[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    missing: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out and not self.missing

    def technical_text(self) -> str:
        parts = ["Command: " + " ".join(self.argv)]
        parts.append("Exit code: %s" % self.returncode)
        if self.stdout:
            parts.append("Output:\n" + self.stdout)
        if self.stderr:
            parts.append("Error output:\n" + self.stderr)
        if self.timed_out:
            parts.append("The command stopped because it took too long.")
        if self.missing:
            parts.append("The command was not found on this system.")
        return "\n\n".join(parts)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def resolve_executable(name_or_path: str) -> Optional[str]:
    if os.path.sep in name_or_path or (os.path.altsep and os.path.altsep in name_or_path):
        return name_or_path if os.path.isfile(name_or_path) and os.access(name_or_path, os.X_OK) else None
    return shutil.which(name_or_path)


def run_command(
    argv: Sequence[str],
    timeout=None,
    check=False,
    user_error="We couldn't complete this operation.",
    cwd=None,
    extra_env=None,
) -> CommandResult:
    if not argv:
        raise AppError(user_error, "No command was provided.")

    executable = resolve_executable(str(argv[0]))
    if executable is None:
        result = CommandResult(
            argv=list(argv),
            returncode=127,
            stdout="",
            stderr="Command not found: %s" % argv[0],
            missing=True,
        )
        if check:
            raise MissingCommandError(
                "This system does not have the tool needed for this step.",
                result.technical_text(),
            )
        return result

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    try:
        completed = subprocess.run(
            list(argv),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            cwd=cwd,
            env=env,
            shell=False,
            text=True,
            errors="replace",
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        result = CommandResult(
            argv=list(argv),
            returncode=-1,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
        )
        if check:
            raise CommandTimeoutError(
                "This operation took too long and was stopped.",
                result.technical_text(),
            )
        return result
    except PermissionError as exc:
        raise PermissionDeniedError(
            "This system did not allow ForensiDrive to run that step.",
            str(exc),
        )
    except OSError as exc:
        raise AppError(user_error, str(exc))

    result = CommandResult(
        argv=list(argv),
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )

    if check and not result.ok:
        if result.returncode in (1, 13) and _looks_like_permission(result):
            raise PermissionDeniedError(
                "This system did not allow ForensiDrive to complete that step.",
                result.technical_text(),
            )
        raise CommandFailedError(user_error, result.technical_text())
    return result


def _looks_like_permission(result: CommandResult) -> bool:
    blob = (result.stderr + " " + result.stdout).lower()
    return "permission denied" in blob or "operation not permitted" in blob
