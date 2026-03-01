import os
import sys
from pathlib import Path
import shutil
from typing import Optional


def _get_home_dir() -> Path:
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return Path(f"/home/{sudo_user}")
    return Path.home()


def expand_path(path: Path) -> Path:
    home = _get_home_dir()
    path_str = str(path)
    if path_str.startswith("~"):
        return home / path_str[2:] if len(path_str) > 1 else home
    return path.expanduser()


def unexpand_path(path: Path) -> Path:
    home = _get_home_dir()
    path_str = str(path.absolute())
    home_str = str(home)
    if path_str.startswith(home_str):
        remainder = path_str[len(home_str):]
        return Path("~" + remainder)
    return path


def absolute_path(path: str | Path) -> Path:
    if isinstance(path, Path):
        path = str(path.absolute())

    if path.startswith("~"):
        return expand_path(Path(path))
    if os.path.isabs(path):
        return Path(path)
    return Path.cwd() / path


def suppress_errors(callback, *args, **kwargs):
    """
    Calls `callback` with the given arguments and suppresses all exceptions.
    Returns the callback's return value if successful, otherwise None.
    """
    try:
        return callback(*args, **kwargs)
    except Exception:
        return None


def delete_path(path: Path) -> None:
    """
    Delete a filesystem path.

    - If it's a symlink: unlink only the link.
    - If it's a directory: recursively delete contents.
    - If it's a file: delete the file.
    """
    if not isinstance(path, Path):
        raise TypeError("path must be a Path instance")

    if not path.exists() and not path.is_symlink():
        return  # nothing to delete

    if path.is_symlink():
        # Only removes the symlink itself, not the target
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        # Regular file (or other non-dir, non-symlink like FIFO)
        path.unlink()


def print_err(*values, sep: Optional[str] = None, end: Optional[str] = None, flush: bool = False):
    print(*values, sep=sep, end=end, flush=flush, file=sys.stderr)
