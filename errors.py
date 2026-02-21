import sys
from enum import IntEnum
from typing import Optional


class ExitCode(IntEnum):
    SUCCESS = 0
    GENERAL_FAILURE = 1
    GIT_NOT_INSTALLED = 2
    NOT_A_GIT_REPO = 3
    NO_REMOTE_ORIGIN = 4


def error(message: str, code: ExitCode = ExitCode.GENERAL_FAILURE) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(code)


def notify(message: str, notify_command: Optional[str]) -> None:
    if notify_command:
        import subprocess

        cmd = notify_command.replace("$!SYM_MESSAGE", message)
        try:
            subprocess.run(cmd, shell=True, check=False)
        except Exception:
            pass


def error_with_notify(
    message: str,
    code: ExitCode = ExitCode.GENERAL_FAILURE,
    notify_command: Optional[str] = None,
) -> None:
    notify(message, notify_command)
    error(message, code)
