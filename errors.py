from pathlib import Path


class GitError(Exception):
    def __init__(self, path: Path):
        self.path = path
        self.message = f"there was a git error at {path}"
        super().__init__(self.message)


class MissingRemoteOrigin(GitError):
    def __init__(self, path: Path):
        super().__init__(path)
        self.message = f"couldn't find remote origin for {path}"


class NotAGitRepo(GitError):
    def __init__(self, path: Path):
        super().__init__(path)
        self.message = f"{path} is not a git repository"


class LinkingError(Exception):
    def __init__(self):
        self.message = "there was an error linking"
        super().__init__(self.message)


class FileAlreadyExist(LinkingError):
    def __init__(self, dest_path: Path):
        super().__init__()
        self.dest_path = dest_path
        self.message = f"couldn't link file existing {dest_path}"


class LinkPermissionDenied(LinkingError):
    def __init__(self, dest_path: Path, creating: bool):
        super().__init__()
        self.dest_path = dest_path
        self.creating = creating
        action = "create" if creating else "remove"
        self.message = f"Permission Error: failed to {action} link at {dest_path}"


class CustomFileException(Exception):
    def __init__(self, path: Path):
        self.path = path
        self.message = f"file exception {path}"
        super().__init__(self.message)


class DirectoryNotFound(CustomFileException):
    def __init__(self, path: Path):
        super().__init__(path)
        self.message = f"directory not found at {path}"


class FileNotDirectory(CustomFileException):
    def __init__(self, path: Path):
        super().__init__(path)
        self.message = f"{path} is a file not a directory"
