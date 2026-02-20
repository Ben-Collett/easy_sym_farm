import os
import fnmatch
import shutil
from typing import List, Set, Optional, Tuple

from errors import LinkError


def get_home_dir() -> str:
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return f"/home/{sudo_user}"
    return os.path.expanduser("~")


def get_source_dir() -> str:
    source = os.environ.get("easy_sym_source")
    if source:
        return os.path.abspath(source)
    return os.path.join(get_home_dir(), "easy_syms")


def get_meta_name() -> str:
    return os.environ.get("easy_sym_meta_name", "easy_env_sym_data.toml")


def is_excluded_by_default(rel_path: str, meta_name: str) -> bool:
    defaults = [".git", ".gitignore", meta_name]
    parts = rel_path.split(os.sep)
    for default in defaults:
        if parts[0] == default or rel_path == default:
            return True
    return False


def matches_pattern(rel_path: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        parts = rel_path.split(os.sep)
        for i in range(len(parts)):
            subpath = os.sep.join(parts[: i + 1])
            if fnmatch.fnmatch(subpath, pattern):
                return True
    return False


def get_all_files_sorted(source_dir: str) -> List[str]:
    all_paths = []
    for root, dirs, files in os.walk(source_dir, topdown=True):
        rel_root = os.path.relpath(root, source_dir)
        if rel_root == ".":
            rel_root = ""
        dirs.sort()
        for d in sorted(dirs):
            if rel_root:
                all_paths.append(os.path.join(rel_root, d))
            else:
                all_paths.append(d)
        for f in sorted(files):
            if rel_root:
                all_paths.append(os.path.join(rel_root, f))
            else:
                all_paths.append(f)
    return sorted(all_paths, key=lambda x: x.count(os.sep))


def is_already_linked_to_source(link_path: str, source_dir: str) -> bool:
    if os.path.islink(link_path):
        target = os.readlink(link_path)
        return target.startswith(source_dir)
    return False


def get_linked_source_path(link_path: str) -> Optional[str]:
    if os.path.islink(link_path):
        return os.readlink(link_path)
    return None


def create_symlink(source: str, dest: str):
    if os.path.islink(dest):
        current_target = os.readlink(dest)
        if current_target == source:
            return
        raise LinkError(
            f"{dest} is a symlink pointing to {current_target}, expected {source}"
        )
    if os.path.isfile(dest):
        raise LinkError(f"{dest} exists and is a regular file")
    if os.path.isdir(dest) and not os.path.islink(dest):
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    os.symlink(source, dest)


def remove_symlink(link_path: str, source_dir: str):
    if os.path.islink(link_path):
        target = os.readlink(link_path)
        if target.startswith(source_dir):
            os.unlink(link_path)


def remove_empty_parents(path: str, stop_at: str):
    parent = os.path.dirname(path)
    while parent != stop_at and parent:
        try:
            if os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)
                parent = os.path.dirname(parent)
            else:
                break
        except OSError:
            break


def collect_linked_descendants(directory: str, source_dir: str) -> List[str]:
    linked = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.islink(full_path):
            target = os.readlink(full_path)
            if target.startswith(source_dir):
                linked.append(full_path)
        elif os.path.isdir(full_path):
            linked.extend(collect_linked_descendants(full_path, source_dir))
    return linked


def move_to_source(
    src_path: str, source_dir: str, rel_dest: str, output_root: str
) -> Tuple[str, str]:
    dest_in_source = os.path.join(source_dir, rel_dest)
    os.makedirs(os.path.dirname(dest_in_source), exist_ok=True)
    shutil.move(src_path, dest_in_source)
    return dest_in_source, src_path
