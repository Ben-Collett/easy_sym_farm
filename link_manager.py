import os
from typing import Optional

from errors import error
from link_utils import (
    check_link_destination,
    create_link,
    ensure_parent_dir,
    expand_path,
    get_existing_symlink_children,
    get_sorted_entries,
    is_descendant_of_symlink,
    matches_any_pattern,
    remove_link,
    remove_empty_parents,
)


class LinkManager:
    DEFAULT_SKIP = [".git", ".gitignore"]

    def __init__(self, source_dir: str, meta_name: str):
        self.source_dir = os.path.abspath(expand_path(source_dir))
        self.meta_name = meta_name
        self._ensure_source_dir()

    def _ensure_source_dir(self) -> None:
        if not os.path.exists(self.source_dir):
            os.makedirs(self.source_dir, exist_ok=True)

    def _get_meta_path(self) -> str:
        return os.path.join(self.source_dir, self.meta_name)

    def _should_skip(self, name: str) -> bool:
        return name in self.DEFAULT_SKIP or name == self.meta_name

    def _get_destination(self, rel_path: str, paths: dict[str, str]) -> Optional[str]:
        if rel_path in paths:
            return paths[rel_path]
        parts = rel_path.split(os.sep)
        for i in range(len(parts) - 1, 0, -1):
            prefix = os.sep.join(parts[:i])
            if prefix in paths:
                suffix = os.sep.join(parts[i:])
                return os.path.join(paths[prefix], suffix)
        return None

    def _unlink_and_link_ancestor(
        self, dest: str, source: str, linked: list[str], unlinked: list[str]
    ) -> None:
        children = get_existing_symlink_children(dest, self.source_dir)
        for child in children:
            if remove_link(child, self.source_dir):
                unlinked.append(child)

    def link(self, paths: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
        linked: list[str] = []
        skipped: list[str] = []
        unlinked: list[str] = []
        sorted_paths = sorted(paths.keys())

        for rel_path in sorted_paths:
            dest = paths[rel_path]
            source = os.path.join(self.source_dir, rel_path)
            if not os.path.exists(source):
                continue
            self._link_path(source, dest, rel_path, paths, linked, skipped, unlinked)

        self._link_remaining(paths, linked, skipped, unlinked)
        return linked, skipped, unlinked

    def _link_path(
        self,
        source: str,
        dest: str,
        rel_path: str,
        paths: dict[str, str],
        linked: list[str],
        skipped: list[str],
        unlinked: list[str],
    ) -> None:
        if is_descendant_of_symlink(dest, self.source_dir):
            skipped.append(rel_path)
            return
        if os.path.isdir(source) and not os.path.islink(source):
            self._link_directory(
                source, dest, rel_path, paths, linked, skipped, unlinked
            )
        else:
            self._link_file(source, dest, rel_path, linked, skipped)

    def _link_directory(
        self,
        source: str,
        dest: str,
        rel_path: str,
        paths: dict[str, str],
        linked: list[str],
        skipped: list[str],
        unlinked: list[str],
    ) -> None:
        result = check_link_destination(dest, source)
        if result == "skip":
            skipped.append(rel_path)
            return
        if result:
            if os.path.isdir(dest) and not os.path.islink(dest):
                self._link_children(
                    source, dest, rel_path, paths, linked, skipped, unlinked
                )
                return
            error(result)
        self._unlink_and_link_ancestor(dest, source, linked, unlinked)
        ensure_parent_dir(dest)
        create_link(dest, source)
        linked.append(rel_path)

    def _link_file(
        self,
        source: str,
        dest: str,
        rel_path: str,
        linked: list[str],
        skipped: list[str],
    ) -> None:
        result = check_link_destination(dest, source)
        if result == "skip":
            skipped.append(rel_path)
            return
        if result:
            error(result)
        ensure_parent_dir(dest)
        create_link(dest, source)
        linked.append(rel_path)

    def _link_children(
        self,
        source: str,
        dest: str,
        rel_path: str,
        paths: dict[str, str],
        linked: list[str],
        skipped: list[str],
        unlinked: list[str],
    ) -> None:
        for entry in get_sorted_entries(source):
            if self._should_skip(entry):
                continue
            child_source = os.path.join(source, entry)
            child_dest = os.path.join(dest, entry)
            child_rel = os.path.join(rel_path, entry)
            self._link_path(
                child_source, child_dest, child_rel, paths, linked, skipped, unlinked
            )

    def _link_remaining(
        self,
        paths: dict[str, str],
        linked: list[str],
        skipped: list[str],
        unlinked: list[str],
    ) -> None:
        linked_set = set(linked)
        skipped_set = set(skipped)
        for entry in get_sorted_entries(self.source_dir):
            if self._should_skip(entry):
                continue
            if entry in linked_set or entry in skipped_set:
                continue
            self._link_entry(entry, paths, linked, skipped, unlinked)

    def _link_entry(
        self,
        entry: str,
        paths: dict[str, str],
        linked: list[str],
        skipped: list[str],
        unlinked: list[str],
    ) -> None:
        source = os.path.join(self.source_dir, entry)
        dest = self._get_destination(entry, paths)
        if dest is None:
            return
        self._link_path(source, dest, entry, paths, linked, skipped, unlinked)

    def unlink(self, pattern: Optional[str] = None) -> list[str]:
        unlinked: list[str] = []
        self._unlink_dir(self.source_dir, pattern, unlinked)
        return unlinked

    def _unlink_dir(
        self, dir_path: str, pattern: Optional[str], unlinked: list[str]
    ) -> None:
        for entry in get_sorted_entries(dir_path):
            full_path = os.path.join(dir_path, entry)
            rel_path = os.path.relpath(full_path, self.source_dir)
            if pattern and not matches_any_pattern(rel_path, [pattern]):
                self._unlink_children_if_dir(full_path, pattern, unlinked)
                continue
            if os.path.isdir(full_path) and not os.path.islink(full_path):
                self._unlink_dir(full_path, pattern, unlinked)
            else:
                dest = self._find_link_destination(rel_path, full_path)
                if dest and remove_link(dest, self.source_dir):
                    unlinked.append(dest)
                    remove_empty_parents(dest, self.source_dir)

    def _unlink_children_if_dir(
        self, path: str, pattern: str, unlinked: list[str]
    ) -> None:
        if os.path.isdir(path) and not os.path.islink(path):
            self._unlink_dir(path, pattern, unlinked)

    def _find_link_destination(self, rel_path: str, source: str) -> Optional[str]:
        from metadata import Metadata

        meta = Metadata(self.source_dir, self.meta_name)
        paths = meta.get_paths()
        dest = self._get_destination(rel_path, paths)
        if dest and os.path.islink(dest):
            from link_utils import is_symlink_to

            if is_symlink_to(dest, source):
                return dest
        return None
