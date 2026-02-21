import os
import subprocess
import time
from datetime import datetime
from typing import Optional

from errors import ExitCode, error, error_with_notify


class GitWrapper:
    def __init__(
        self,
        repo_path: str,
        retry_delay_ms: int = 6000,
        max_attempts: int = 10,
        notify_command: Optional[str] = None,
    ):
        self.repo_path = repo_path
        self.retry_delay_ms = retry_delay_ms
        self.max_attempts = max_attempts
        self.notify_command = notify_command

    def _run_git(
        self, args: list[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check,
        )

    def is_git_installed(self) -> bool:
        try:
            subprocess.run(
                ["git", "--version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_git_repo(self) -> bool:
        try:
            self._run_git(["rev-parse", "--git-dir"])
            return True
        except subprocess.CalledProcessError:
            return False

    def has_remote_origin(self) -> bool:
        try:
            result = self._run_git(["remote"])
            return "origin" in result.stdout.splitlines()
        except subprocess.CalledProcessError:
            return False

    def get_porcelain_status(self) -> list[tuple[str, str]]:
        result = self._run_git(["status", "--porcelain"])
        status_lines = []
        for line in result.stdout.strip().split("\n"):
            if line:
                status = line[:2]
                path = line[3:]
                status_lines.append((status, path))
        return status_lines

    def get_new_and_deleted_files(self, no_new_files_dirs: list[str]) -> list[str]:
        status_lines = self.get_porcelain_status()
        problematic = []
        for status, path in status_lines:
            is_new = status.startswith("??") or status.startswith("A ")
            is_deleted = "D" in status
            if is_new or is_deleted:
                for no_new_dir in no_new_files_dirs:
                    if path.startswith(no_new_dir) or path == no_new_dir:
                        problematic.append(path)
                        break
        return problematic

    def has_unstaged_changes(self) -> bool:
        status_lines = self.get_porcelain_status()
        return len(status_lines) > 0

    def get_changed_paths(self) -> list[str]:
        status_lines = self.get_porcelain_status()
        return [path for _, path in status_lines]

    def add_all(self) -> None:
        self._run_git(["add", "-A"])

    def commit(self, message: Optional[str] = None) -> bool:
        if message is None:
            message = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._run_git(["commit", "-m", message])
            return True
        except subprocess.CalledProcessError:
            return False

    def _is_network_error(self, stderr: str) -> bool:
        network_errors = [
            "Could not resolve host",
            "Connection timed out",
            "Failed to connect",
        ]
        return any(err in stderr for err in network_errors)

    def push(self) -> tuple[bool, str]:
        attempts = 0
        while attempts < self.max_attempts:
            try:
                self._run_git(["push"])
                return True, "Push successful"
            except subprocess.CalledProcessError as e:
                stderr = e.stderr or ""
                if self._is_network_error(stderr):
                    attempts += 1
                    if attempts < self.max_attempts:
                        time.sleep(self.retry_delay_ms / 1000)
                else:
                    return False, f"Push failed: {stderr}"
        return False, "Push failed: max retry attempts reached"

    def push_with_notify(self) -> None:
        success, message = self.push()
        error_with_notify(message, ExitCode.GENERAL_FAILURE, self.notify_command)

    def add_to_gitignore(self, pattern: str) -> None:
        gitignore_path = os.path.join(self.repo_path, ".gitignore")
        with open(gitignore_path, "a") as f:
            f.write(f"{pattern}\n")

    def remove_from_gitignore(self, pattern: str) -> None:
        gitignore_path = os.path.join(self.repo_path, ".gitignore")
        if not os.path.exists(gitignore_path):
            return
        with open(gitignore_path, "r") as f:
            lines = f.readlines()
        with open(gitignore_path, "w") as f:
            for line in lines:
                if line.strip() != pattern:
                    f.write(line)

    def check_preconditions(self) -> None:
        if not self.is_git_installed():
            error("git not installed", ExitCode.GIT_NOT_INSTALLED)
        if not self.is_git_repo():
            error("not a git repository", ExitCode.NOT_A_GIT_REPO)
        if not self.has_remote_origin():
            error("no remote origin found", ExitCode.NO_REMOTE_ORIGIN)
