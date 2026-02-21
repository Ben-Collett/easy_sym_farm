import os
import shutil
import sys
from fnmatch import fnmatch

from errors import error
from git_wrapper import GitWrapper
from link_manager import LinkManager
from link_utils import expand_path, get_home_dir, matches_any_pattern
from metadata import Metadata


def get_source_dir() -> str:
    source = os.environ.get("easy_sym_source")
    if source:
        return expand_path(source)
    return os.path.join(get_home_dir(), "easy_syms")


def get_meta_name() -> str:
    return os.environ.get("easy_sym_meta_name", "easy_env_sym_data.toml")


def cmd_help() -> None:
    help_text = """easy_sym_farm - symlink farm manager

Usage: easy_env_sym <command> [arguments]

Commands:
  help, -h                    Show this help message
  link                        Symlink files from source directory
  unlink [pattern]            Unlink symlinked files (optionally matching pattern)
  push                        Git add, commit, and push changes
  add <path> [group_dir]      Add file/dir to source and link it
  add-to-git-ignore <pattern> Add pattern to .gitignore
  remove-from-git-ignore <pattern> Remove pattern from .gitignore
  add-to-no-update <pattern>  Add pattern to no-update-on list
  remove-from-no-update <pattern> Remove pattern from no-update-on list
  add-to-no-new-files <path>  Add path to no-new-files list
  remove-from-no-new-files <path> Remove path from no-new-files list
  set source <path>           Set source directory path
  set meta-name <name>        Set metadata file name
  set <tag> <setting> <value> Set any config value

Environment variables:
  easy_sym_source      Source directory (default: ~/easy_syms)
  easy_sym_meta_name   Metadata file name (default: easy_env_sym_data.toml)"""
    print(help_text)


def cmd_link() -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    manager = LinkManager(source_dir, meta_name)
    meta = Metadata(source_dir, meta_name)
    paths = meta.get_paths()
    linked, skipped, unlinked = manager.link(paths)
    print(
        f"Linked: {len(linked)}, Skipped: {len(skipped)}, Unlinked ancestors: {len(unlinked)}"
    )


def cmd_unlink(pattern: str | None = None) -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    manager = LinkManager(source_dir, meta_name)
    unlinked = manager.unlink(pattern)
    print(f"Unlinked: {len(unlinked)}")


def cmd_push() -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    meta = Metadata(source_dir, meta_name)
    git = GitWrapper(
        source_dir,
        meta.get_retry_delay_ms(),
        meta.get_max_attempts(),
        meta.get_push_notify_command(),
    )
    git.check_preconditions()
    no_new_files = meta.get_no_new_files()
    if no_new_files:
        problematic = git.get_new_and_deleted_files(no_new_files)
        if problematic:
            error(
                f"new/deleted files in no-new-files directories: {', '.join(problematic)}"
            )
    changed_paths = git.get_changed_paths()
    no_update_patterns = meta.get_no_update_on()
    if changed_paths:
        all_match = all(
            matches_any_pattern(p, no_update_patterns) for p in changed_paths
        )
        if all_match:
            print("All changes match no-update-on patterns, skipping push")
            return
    if not git.has_unstaged_changes():
        print("No changes to commit")
        return
    git.add_all()
    if not git.commit():
        print("Nothing to commit")
        return
    git.push_with_notify()
    print("Pushed successfully")


def _get_unique_name(dest: str, source_dir: str) -> str:
    base = os.path.basename(dest)
    name, ext = os.path.splitext(base)
    counter = 0
    while True:
        if counter == 0:
            candidate = name + ext
        else:
            candidate = f"{name}_{counter}{ext}"
        if not os.path.exists(os.path.join(source_dir, candidate)):
            return candidate
        counter += 1


def cmd_add(path: str, group_dir: str | None = None) -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    abs_path = expand_path(path)
    if os.path.islink(abs_path):
        error(f"cannot add symlink: {abs_path}")
    rel_name = os.path.basename(abs_path)
    if group_dir:
        target_subdir = os.path.join(source_dir, group_dir)
        os.makedirs(target_subdir, exist_ok=True)
        unique_name = rel_name
        dest_in_source = os.path.join(target_subdir, unique_name)
        if os.path.exists(dest_in_source):
            unique_name = _get_unique_name(abs_path, target_subdir)
            dest_in_source = os.path.join(target_subdir, unique_name)
        rel_path = os.path.join(group_dir, unique_name)
    else:
        unique_name = _get_unique_name(abs_path, source_dir)
        dest_in_source = os.path.join(source_dir, unique_name)
        rel_path = unique_name
    shutil.move(abs_path, dest_in_source)
    meta = Metadata(source_dir, meta_name)
    original_parent = os.path.dirname(abs_path)
    meta.set_path(rel_path, original_parent)
    manager = LinkManager(source_dir, meta_name)
    paths = meta.get_paths()
    manager.link(paths)
    print(f"Added {rel_path} -> {original_parent}")


def cmd_add_to_git_ignore(pattern: str) -> None:
    source_dir = get_source_dir()
    git = GitWrapper(source_dir)
    git.add_to_gitignore(pattern)
    print(f"Added '{pattern}' to .gitignore")


def cmd_remove_from_git_ignore(pattern: str) -> None:
    source_dir = get_source_dir()
    git = GitWrapper(source_dir)
    git.remove_from_gitignore(pattern)
    print(f"Removed '{pattern}' from .gitignore")


def cmd_add_to_no_update(pattern: str) -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    meta = Metadata(source_dir, meta_name)
    meta.add_to_list("general", "no-update-on", pattern)
    print(f"Added '{pattern}' to no-update-on")


def cmd_remove_from_no_update(pattern: str) -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    meta = Metadata(source_dir, meta_name)
    meta.remove_from_list("general", "no-update-on", pattern)
    print(f"Removed '{pattern}' from no-update-on")


def cmd_add_to_no_new_files(path: str) -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    meta = Metadata(source_dir, meta_name)
    meta.add_to_list("general", "no-new-files", path)
    print(f"Added '{path}' to no-new-files")


def cmd_remove_from_no_new_files(path: str) -> None:
    source_dir = get_source_dir()
    meta_name = get_meta_name()
    meta = Metadata(source_dir, meta_name)
    meta.remove_from_list("general", "no-new-files", path)
    print(f"Removed '{path}' from no-new-files")


def cmd_set(args: list[str]) -> None:
    if len(args) < 2:
        error("set requires at least 2 arguments")
    if args[0] == "source":
        cmd_unlink()
        os.environ["easy_sym_source"] = expand_path(args[1])
        cmd_link()
        print(f"Set source to {args[1]}")
    elif args[0] == "meta-name":
        os.environ["easy_sym_meta_name"] = args[1]
        print(f"Set meta-name to {args[1]}")
    elif len(args) >= 3:
        source_dir = get_source_dir()
        meta_name = get_meta_name()
        meta = Metadata(source_dir, meta_name)
        meta.set_value(args[0], args[1], " ".join(args[2:]))
        print(f"Set {args[0]}.{args[1]} = {' '.join(args[2:])}")
    else:
        error("invalid set command")


def main(args: list[str]) -> None:
    if not args or args[0] in ["help", "-h"]:
        cmd_help()
        return
    cmd = args[0]
    if cmd == "link":
        cmd_link()
    elif cmd == "unlink":
        pattern = args[1] if len(args) > 1 else None
        cmd_unlink(pattern)
    elif cmd == "push":
        cmd_push()
    elif cmd == "add":
        if len(args) < 2:
            error("add requires at least 1 argument")
        group_dir = args[2] if len(args) > 2 else None
        cmd_add(args[1], group_dir)
    elif cmd == "add-to-git-ignore":
        if len(args) < 2:
            error("add-to-git-ignore requires pattern argument")
        cmd_add_to_git_ignore(args[1])
    elif cmd == "remove-from-git-ignore":
        if len(args) < 2:
            error("remove-from-git-ignore requires pattern argument")
        cmd_remove_from_git_ignore(args[1])
    elif cmd == "add-to-no-update":
        if len(args) < 2:
            error("add-to-no-update requires pattern argument")
        cmd_add_to_no_update(args[1])
    elif cmd == "remove-from-no-update":
        if len(args) < 2:
            error("remove-from-no-update requires pattern argument")
        cmd_remove_from_no_update(args[1])
    elif cmd == "add-to-no-new-files":
        if len(args) < 2:
            error("add-to-no-new-files requires path argument")
        cmd_add_to_no_new_files(args[1])
    elif cmd == "remove-from-no-new-files":
        if len(args) < 2:
            error("remove-from-no-new-files requires path argument")
        cmd_remove_from_no_new_files(args[1])
    elif cmd == "set":
        if len(args) < 2:
            error("set requires arguments")
        cmd_set(args[1:])
    else:
        error(f"unknown command: {cmd}")
