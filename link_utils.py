import os
import stat
from fnmatch import fnmatch
from typing import Optional


def get_home_dir() -> str:
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        import pwd

        return pwd.getpwnam(sudo_user).pw_dir
    return os.path.expanduser("~")


def expand_path(path: str) -> str:
    if path.startswith("~"):
        return os.path.join(
            get_home_dir(), path[2:] if path.startswith("~/") else path[1:]
        )
    return os.path.abspath(path)


def is_symlink_to(path: str, target: str) -> bool:
    if not os.path.islink(path):
        return False
    try:
        link_target = os.readlink(path)
        return os.path.abspath(link_target) == os.path.abspath(target)
    except OSError:
        return False


def is_descendant_of_symlink(path: str, source_dir: str) -> bool:
    parent = os.path.dirname(path)
    while parent and parent != "/":
        if os.path.islink(parent):
            link_target = os.readlink(parent)
            if os.path.abspath(link_target).startswith(os.path.abspath(source_dir)):
                return True
        parent = os.path.dirname(parent)
    return False


def get_existing_symlink_children(dest_dir: str, source_dir: str) -> list[str]:
    if not os.path.isdir(dest_dir):
        return []
    children = []
    for item in os.listdir(dest_dir):
        item_path = os.path.join(dest_dir, item)
        if os.path.islink(item_path):
            link_target = os.readlink(item_path)
            if os.path.abspath(link_target).startswith(os.path.abspath(source_dir)):
                children.append(item_path)
    return children


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def remove_empty_parents(path: str, stop_at: str) -> None:
    parent = os.path.dirname(path)
    while parent and parent != stop_at and len(parent) > len(stop_at):
        if os.path.isdir(parent) and not os.listdir(parent):
            os.rmdir(parent)
            parent = os.path.dirname(parent)
        else:
            break


def check_link_destination(dest: str, source: str) -> Optional[str]:
    if not os.path.lexists(dest):
        return None
    if os.path.islink(dest):
        if is_symlink_to(dest, source):
            return "skip"
        return f"symlink at {dest} points elsewhere"
    if os.path.isfile(dest):
        return f"regular file exists at {dest}"
    return None


def create_link(dest: str, source: str) -> None:
    ensure_parent_dir(dest)
    os.symlink(os.path.abspath(source), dest)


def remove_link(link_path: str, source_dir: str) -> bool:
    if not os.path.islink(link_path):
        return False
    link_target = os.readlink(link_path)
    if os.path.abspath(link_target).startswith(os.path.abspath(source_dir)):
        os.unlink(link_path)
        return True
    return False


def matches_pattern(path: str, pattern: str) -> bool:
    return fnmatch(path, pattern)


def matches_any_pattern(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, p) for p in patterns)


def get_sorted_entries(dir_path: str) -> list[str]:
    try:
        entries = os.listdir(dir_path)
        return sorted(entries)
    except OSError:
        return []
