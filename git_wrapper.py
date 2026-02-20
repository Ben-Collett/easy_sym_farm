import subprocess
import shutil
from datetime import datetime
from typing import List, Tuple, Optional
import fnmatch

from errors import (
    GitNotInstalledError,
    NotAGitRepoError,
    NoRemoteOriginError,
    NetworkError,
    EasySymError,
    NO_REMOTE_ORIGIN,
)


class GitWrapper:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self._check_git_installed()
        self._check_is_git_repo()

    def _check_git_installed(self):
        if shutil.which("git") is None:
            raise GitNotInstalledError()

    def _check_is_git_repo(self):
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise NotAGitRepoError()

    def has_remote_origin(self) -> bool:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def get_status_porcelain(self) -> List[Tuple[str, str]]:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        statuses = []
        for line in result.stdout.strip().split("\n"):
            if line:
                status = line[:2]
                path = line[3:]
                statuses.append((status, path))
        return statuses

    def get_unstaged_changes(self) -> List[Tuple[str, str]]:
        all_changes = self.get_status_porcelain()
        return [
            (status, path)
            for status, path in all_changes
            if status.startswith("??")
            or "D" in status
            or "M" in status
            or "A" in status
        ]

    def get_new_files(self) -> List[str]:
        changes = self.get_status_porcelain()
        return [path for status, path in changes if status.startswith("??")]

    def get_deleted_files(self) -> List[str]:
        changes = self.get_status_porcelain()
        return [path for status, path in changes if "D" in status]

    def files_match_patterns(self, files: List[str], patterns: List[str]) -> bool:
        if not patterns:
            return not files
        for f in files:
            matches = any(fnmatch.fnmatch(f, p) for p in patterns)
            if not matches:
                return False
        return True

    def add_all(self):
        subprocess.run(
            ["git", "add", "."],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

    def add_path(self, path: str):
        subprocess.run(
            ["git", "add", path],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

    def commit(self, message: str):
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

    def has_changes_to_commit(self) -> bool:
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=self.repo_path,
            capture_output=True,
        )
        return result.returncode != 0

    def push(self) -> Tuple[bool, str]:
        result = subprocess.run(
            ["git", "push"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, ""
        stderr = result.stderr.lower()
        if any(
            msg in stderr
            for msg in [
                "could not resolve host",
                "connection timed out",
                "failed to connect",
            ]
        ):
            return False, "network"
        return False, "other"

    def get_commit_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_to_gitignore(self, pattern: str):
        gitignore_path = f"{self.repo_path}/.gitignore"
        with open(gitignore_path, "a+") as f:
            f.seek(0)
            content = f.read()
            if pattern not in content:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(f"{pattern}\n")

    def remove_from_gitignore(self, pattern: str):
        gitignore_path = f"{self.repo_path}/.gitignore"
        try:
            with open(gitignore_path, "r") as f:
                lines = f.readlines()
            with open(gitignore_path, "w") as f:
                for line in lines:
                    if line.strip() != pattern:
                        f.write(line)
        except FileNotFoundError:
            pass
