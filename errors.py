SUCCESS = 0
GENERAL_FAILURE = 1
GIT_NOT_INSTALLED = 2
NOT_A_GIT_REPO = 3
NO_REMOTE_ORIGIN = 4


class EasySymError(Exception):
    def __init__(self, message: str, exit_code: int = GENERAL_FAILURE):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class GitNotInstalledError(EasySymError):
    def __init__(self):
        super().__init__("git not installed", GIT_NOT_INSTALLED)


class NotAGitRepoError(EasySymError):
    def __init__(self):
        super().__init__("not a git repository", NOT_A_GIT_REPO)


class NoRemoteOriginError(EasySymError):
    def __init__(self):
        super().__init__("no remote origin found", NO_REMOTE_ORIGIN)


class LinkError(EasySymError):
    def __init__(self, message: str):
        super().__init__(message, GENERAL_FAILURE)


class ConfigError(EasySymError):
    def __init__(self, message: str):
        super().__init__(message, GENERAL_FAILURE)


class NetworkError(EasySymError):
    def __init__(self, message: str):
        super().__init__(message, GENERAL_FAILURE)


def exit_with_error(error: EasySymError):
    import sys

    sys.stderr.write(f"Error: {error.message}\n")
    sys.exit(error.exit_code)
