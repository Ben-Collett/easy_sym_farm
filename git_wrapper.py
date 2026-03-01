from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from subprocess import CompletedProcess

from errors import (
    DirectoryNotFound,
    FileNotDirectory,
    GitError,
    MissingRemoteOrigin,
    NotAGitRepo,
)


class StatusChangeType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class FileChangeStatus:
    def __init__(self, relative_path: str, change_type: StatusChangeType):
        self.relative_path = relative_path
        self.change_type = change_type


class GitPushStatus(Enum):
    Success = "success"
    NetworkError = "network_error"


class GitWrapper:
    def __init__(self, path: Path):
        self.path = path

    def _validate_path(self) -> None:
        if not self.path.exists():
            raise DirectoryNotFound(self.path)
        if not self.path.is_dir():
            raise FileNotDirectory(self.path)
        if not (self.path / ".git").exists():
            raise NotAGitRepo(self.path)

    def _run_git(self, *args: str) -> CompletedProcess:
        import subprocess

        self._validate_path()
        result = subprocess.run(
            ["git", *args],
            cwd=self.path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GitError(self.path)
        return result

    def changes(
        self, ignored_glob_patterns: Optional[list[str]] = None
    ) -> list[FileChangeStatus]:
        result = self._run_git("status", "--porcelain")
        output = result.stdout

        if not output.strip():
            return []

        changes: list[FileChangeStatus] = []

        import fnmatch

        for line in output.splitlines():
            if len(line) < 3:
                continue
            status_code = line[:2]
            relative_path = line[3:]

            if status_code[0] == "?" or status_code[1] == "?":
                change_type = StatusChangeType.ADDED
            elif status_code[0] == "A" or status_code[1] == "A":
                change_type = StatusChangeType.ADDED
            elif status_code[0] == "D" or status_code[1] == "D":
                change_type = StatusChangeType.REMOVED
            else:
                change_type = StatusChangeType.MODIFIED

            if ignored_glob_patterns:
                should_ignore = False
                for pattern in ignored_glob_patterns:
                    if fnmatch.fnmatch(relative_path, pattern):
                        should_ignore = True
                        break
                if should_ignore:
                    continue

            changes.append(FileChangeStatus(relative_path, change_type))

        return changes

    def add_all(self) -> None:
        self._run_git("add", ".")

    def push(self) -> GitPushStatus:
        result = self._run_git("push")

        if result.returncode != 0:
            error_lower = result.stderr.lower()
            if (
                "network" in error_lower
                or "connection" in error_lower
                or "could not resolve host" in error_lower
            ):
                return GitPushStatus.NetworkError
            raise GitError(self.path)

        return GitPushStatus.Success

    def timestamped_commit(self) -> None:
        timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        self._run_git("commit", "-m", timestamp)

        self._validate_path()

        remote_result = self._run_git(
            "remote", "get-url", "origin"
        )
        if remote_result.returncode != 0:
            raise MissingRemoteOrigin(self.path)
