import os
import time
import subprocess
import shutil
from typing import List, Optional, Any, Set

from config import Config
from errors import EasySymError, LinkError, NoRemoteOriginError
from git_wrapper import GitWrapper
import link_utils
import fnmatch


class CommandHandler:
    def __init__(self):
        self.config = Config()
        self._git: Optional[GitWrapper] = None

    @property
    def git(self) -> GitWrapper:
        if self._git is None:
            self._git = GitWrapper(self.config.source_dir)
        return self._git

    def link(self):
        all_paths = link_utils.get_all_files_sorted(self.config.source_dir)
        linked_dirs: Set[str] = set()
        for rel_path in all_paths:
            if self._should_skip_path(rel_path, linked_dirs):
                continue
            source_full = os.path.join(self.config.source_dir, rel_path)
            dest_full = self.config.get_destination_path(rel_path)
            if os.path.isdir(source_full) and not os.path.islink(source_full):
                self._link_directory(rel_path, source_full, dest_full, linked_dirs)
            else:
                self._link_file(source_full, dest_full)

    def _should_skip_path(self, rel_path: str, linked_dirs: Set[str]) -> bool:
        if link_utils.is_excluded_by_default(rel_path, self.config.meta_name):
            return True
        if link_utils.matches_pattern(rel_path, self.config.no_sym):
            return True
        for linked_dir in linked_dirs:
            if rel_path.startswith(linked_dir + os.sep) or rel_path == linked_dir:
                return True
        return False

    def _unlink_linked_descendants(self, directory: str):
        if not os.path.isdir(directory):
            return
        for item in sorted(os.listdir(directory)):
            full_path = os.path.join(directory, item)
            if os.path.islink(full_path):
                target = os.readlink(full_path)
                if target.startswith(self.config.source_dir):
                    os.unlink(full_path)
            elif os.path.isdir(full_path):
                self._unlink_linked_descendants(full_path)

    def _link_directory(
        self, rel_path: str, source_full: str, dest_full: str, linked_dirs: Set[str]
    ):
        if os.path.islink(dest_full):
            target = os.readlink(dest_full)
            if target == source_full:
                linked_dirs.add(rel_path)
                return
            raise LinkError(f"{dest_full} is a symlink pointing elsewhere: {target}")
        if os.path.isdir(dest_full):
            self._unlink_linked_descendants(dest_full)
            return
        self._unlink_linked_ancestors_of(rel_path)
        os.makedirs(os.path.dirname(dest_full), exist_ok=True)
        os.symlink(source_full, dest_full)
        linked_dirs.add(rel_path)

    def _unlink_linked_ancestors_of(self, rel_path: str):
        parts = rel_path.split(os.sep)
        for i in range(len(parts) - 1):
            ancestor = os.sep.join(parts[: i + 1])
            ancestor_dest = self.config.get_destination_path(ancestor)
            if os.path.islink(ancestor_dest):
                target = os.readlink(ancestor_dest)
                if target.startswith(self.config.source_dir):
                    os.unlink(ancestor_dest)

    def _link_file(self, source_full: str, dest_full: str):
        if os.path.islink(dest_full):
            target = os.readlink(dest_full)
            if target == source_full:
                return
            raise LinkError(f"{dest_full} already points to {target}")
        if os.path.exists(dest_full):
            raise LinkError(f"{dest_full} exists and is not a symlink")
        os.makedirs(os.path.dirname(dest_full), exist_ok=True)
        os.symlink(source_full, dest_full)

    def unlink(self, pattern: Optional[str] = None):
        self._unlink_from_root(self.config.output_root_target, pattern)
        for override_path in self.config.path_overrides.values():
            if os.path.islink(override_path):
                target = os.readlink(override_path)
                if target.startswith(self.config.source_dir):
                    os.unlink(override_path)

    def _unlink_from_root(self, directory: str, pattern: Optional[str]):
        if not os.path.isdir(directory):
            return
        items = sorted(os.listdir(directory))
        for item in items:
            full_path = os.path.join(directory, item)
            if os.path.islink(full_path):
                self._maybe_unlink(full_path, pattern)
            elif os.path.isdir(full_path):
                self._unlink_from_root(full_path, pattern)

    def _maybe_unlink(self, full_path: str, pattern: Optional[str]):
        target = os.readlink(full_path)
        if not target.startswith(self.config.source_dir):
            return
        rel_path = os.path.relpath(full_path, self.config.output_root_target)
        if pattern is None or fnmatch.fnmatch(rel_path, pattern):
            os.unlink(full_path)
            link_utils.remove_empty_parents(full_path, self.config.output_root_target)

    def push(self):
        if not self.git.has_remote_origin():
            raise NoRemoteOriginError()
        self._check_no_new_files_violations()
        changes = self.git.get_unstaged_changes()
        changed_files = [path for _, path in changes]
        if not changed_files:
            return
        if self._all_changes_skip_push(changed_files):
            return
        self.git.add_all()
        if not self.git.has_changes_to_commit():
            return
        self.git.commit(self.git.get_commit_timestamp())
        self._push_with_retry()

    def _check_no_new_files_violations(self):
        for no_new_dir in self.config.no_new_files:
            new_files = self.git.get_new_files()
            deleted_files = self.git.get_deleted_files()
            for f in new_files + deleted_files:
                if f.startswith(no_new_dir + "/") or f == no_new_dir:
                    raise EasySymError(f"no-new-files violation in {no_new_dir}")

    def _all_changes_skip_push(self, changed_files: List[str]) -> bool:
        if not self.config.no_update_on:
            return False
        return self.git.files_match_patterns(changed_files, self.config.no_update_on)

    def _push_with_retry(self):
        attempts = 0
        max_attempts = self.config.max_attempts
        delay_ms = self.config.retry_delay_ms
        last_error = None
        while attempts < max_attempts:
            success, error_type = self.git.push()
            if success:
                self._notify_if_set("Successfully pushed changes")
                return
            if error_type != "network":
                last_error = EasySymError(f"Push failed: {error_type}")
                break
            attempts += 1
            if attempts < max_attempts:
                time.sleep(delay_ms / 1000)
        if last_error is None:
            last_error = EasySymError("Push failed after max retries")
        self._notify_if_set(last_error.message)
        raise last_error

    def _notify_if_set(self, message: str):
        cmd_str = self.config.push_notify_command
        if cmd_str:
            cmd = cmd_str.replace("$!SYM_MESSAGE", message)
            subprocess.run(cmd, shell=True)

    def add(self, args: List[str]):
        if len(args) == 1:
            self._add_single(args[0])
        elif len(args) == 2:
            self._add_with_override(args[0], args[1])
        else:
            raise EasySymError("add requires 1 or 2 arguments")

    def _add_single(self, path: str):
        abs_path = os.path.abspath(path)
        if not abs_path.startswith(self.config.output_root_target):
            raise EasySymError(f"{path} is not under output root target")
        rel_path = os.path.relpath(abs_path, self.config.output_root_target)
        dest_in_source = os.path.join(self.config.source_dir, rel_path)
        os.makedirs(os.path.dirname(dest_in_source), exist_ok=True)
        shutil.move(abs_path, dest_in_source)
        os.symlink(dest_in_source, abs_path)

    def _add_with_override(self, rel_source_path: str, target_path: str):
        abs_target = os.path.abspath(target_path)
        rel_source_path = rel_source_path.lstrip("/")
        dest_in_source = os.path.join(self.config.source_dir, rel_source_path)
        os.makedirs(os.path.dirname(dest_in_source), exist_ok=True)
        shutil.move(abs_target, dest_in_source)
        self.config.add_path_override(rel_source_path, abs_target)
        self.config.save()
        os.symlink(dest_in_source, abs_target)

    def add_to_git_ignore(self, pattern: str):
        self.git.add_to_gitignore(pattern)

    def remove_from_git_ignore(self, pattern: str):
        self.git.remove_from_gitignore(pattern)

    def add_to_no_update(self, pattern: str):
        self.config.add_to_list("general", "no-update-on", pattern)
        self.config.save()

    def remove_from_no_update(self, pattern: str):
        self.config.remove_from_list("general", "no-update-on", pattern)
        self.config.save()

    def add_to_no_new_files(self, path: str):
        self.config.add_to_list("general", "no-new-files", path)
        self.config.save()

    def remove_from_no_new_files(self, path: str):
        self.config.remove_from_list("general", "no-new-files", path)
        self.config.save()

    def add_to_no_sym(self, pattern: str):
        self.config.add_to_list("general", "no-sym", pattern)
        self.config.save()

    def remove_from_no_sym(self, pattern: str):
        self.config.remove_from_list("general", "no-sym", pattern)
        self.config.save()

    def set_source(self, path: str):
        self.unlink()
        abs_path = os.path.abspath(path)
        os.environ["easy_sym_source"] = abs_path
        self.config = Config(abs_path)
        self._git = GitWrapper(abs_path)
        self.link()

    def set_meta_name(self, name: str):
        os.environ["easy_sym_meta_name"] = name
        self.config = Config()

    def set_config_value(self, tag: str, setting: str, value: Any):
        str_val = str(value)
        final_value: Any = value
        if str_val.lower() == "true":
            final_value = True
        elif str_val.lower() == "false":
            final_value = False
        elif str_val.isdigit():
            final_value = int(str_val)
        self.config.set_value(tag, setting, final_value)
        self.config.save()
