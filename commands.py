import fnmatch
from pathlib import Path
import shutil
from utils import print_err, delete_path, suppress_errors
from ansii import RED, RESET, BLUE, BOLD, GREEN
import sys
import subprocess
import time

from config import Config
from git_wrapper import GitPushStatus, GitWrapper
from linker import link, unlink, LinkData


def _safe_move_dir(origin: Path, target: Path):
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(origin.absolute()), str(target.absolute()))
    except FileNotFoundError:
        print_err(
            f"{RED}{BOLD}FILE NOT FOUND{RESET}{RED}, can't add {BOLD}{BLUE}{
                origin.absolute()
            }{RED} {RESET}"
        )
        suppress_errors(delete_path, origin)
        exit(1)
    except PermissionError:
        print_err(
            f"{RED}{BOLD}PERMISSION DENIED{RESET}{RED}, can't add {BOLD}{BLUE}{
                origin.absolute()
            }{RED} {RESET}"
        )
        suppress_errors(delete_path, origin)
        exit(1)
    except Exception as e:
        print_err(e)
        suppress_errors(delete_path, origin)
        exit(1)


def _linked_message(source, target):
    return f"linked {BOLD}{GREEN}{source}{RESET} to {BLUE}{BOLD}{target}{RESET}"


class CommandProcessor:
    def __init__(self, config: Config):
        self.config = config

    def link_all(self) -> None:
        source_dir = Config.get_source_directory()
        abs_paths = self.config.get_absolute_paths()

        for source_rel, target_str in abs_paths.items():
            source_path = source_dir / source_rel
            target_path = Path(target_str)
            data: LinkData = link(source_path, target_path)
            if data.msg:
                print(data.msg)
            elif not data.already_linked:
                print(_linked_message(source_path, target_path))

    def unlink_all(self) -> None:
        abs_paths = self.config.get_absolute_paths()

        for source_rel, target_str in abs_paths.items():
            source_path = Config.get_source_directory() / source_rel
            msg = unlink(source_path, self.config)
            if msg:
                print(msg)
            else:
                print(f"unlinked {BLUE}{BOLD}{source_path}{RESET}")

    def unlink_source_match_pattern(self, pattern: str) -> None:
        abs_paths = self.config.get_absolute_paths()

        for source_rel, target_str in abs_paths.items():
            if fnmatch.fnmatch(source_rel, pattern):
                source_path = Config.get_source_directory() / source_rel
                msg = unlink(source_path, self.config)
                if msg:
                    print(msg)

    def push(self) -> None:
        source_dir = Config.get_source_directory()
        git = GitWrapper(source_dir)

        changes = git.changes(self.config.no_update_on)
        if not changes:
            return

        for change in changes:
            for no_update_pattern in self.config.no_update_on:
                if fnmatch.fnmatch(change.relative_path, no_update_pattern):
                    break
            else:
                break
        else:
            return

        for no in self.config.no_new_files:
            no_new_path = source_dir / no
            if no_new_path.exists():
                for change in changes:
                    if str(change.relative_path).startswith(no):
                        error_msg = f"File added in no-new-files directory: {
                            change.relative_path
                        }"
                        print(error_msg, file=sys.stderr)
                        if self.config.push_notify_command:
                            notify_cmd = self.config.push_notify_command.replace(
                                "$!SYM_MESSAGE", error_msg
                            )
                            subprocess.run(notify_cmd, shell=True)
                        return

        attempts = 0
        max_attempts = self.config.max_attempts
        retry_delays_ms = self.config.retry_delays_ms

        while attempts < max_attempts:
            git.add_all()
            git.timestamped_commit()
            status = git.push()

            if status == GitPushStatus.Success:
                return
            elif status == GitPushStatus.NetworkError:
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(retry_delays_ms / 1000.0)
                    continue
                else:
                    error_msg = "Network error: max retry attempts reached"
                    print(error_msg, file=sys.stderr)
                    if self.config.push_notify_command:
                        notify_cmd = self.config.push_notify_command.replace(
                            "$!SYM_MESSAGE", error_msg
                        )
                        subprocess.run(notify_cmd, shell=True)

    def add(self, path: Path) -> None:
        source_dir = Config.get_source_directory()
        source_path = source_dir / path.name
        if source_path.resolve() == path.resolve():
            print("already linked")
            exit(0)
        if source_path.exists():
            counter = 1
            stem = path.stem
            suffix = path.suffix
            while source_path.exists():
                source_path = source_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        _safe_move_dir(path, source_path)
        data = link(source_path, path)
        msg = data.msg
        if msg:
            print_err(msg)
            exit(1)
        else:
            print(_linked_message(source_path, path))

        rel_path = source_path.relative_to(source_dir)
        target = str(path)
        self.config.add_to_paths(str(rel_path), target)
        self.config.write()

    def add_path_and_group(self, path: Path, group_path: str) -> None:
        source_dir = Config.get_source_directory()

        if ".." in group_path:
            group_parts = group_path.split("/")
            for part in group_parts:
                if part == "..":
                    raise ValueError(
                        "Group path cannot escape source directory")

        group_dir = source_dir / group_path
        group_dir.mkdir(parents=True, exist_ok=True)

        target_path = group_dir / path.name
        if target_path.resolve() == path.resolve():
            print("already linked")
            exit(0)

        if target_path.exists():
            counter = 1
            stem = path.stem
            suffix = path.suffix
            while target_path.exists():
                target_path = group_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        _safe_move_dir(path, target_path)
        data = link(target_path, path)
        msg = data.msg
        if msg:
            print_err(msg)
            exit(1)
        else:
            print(_linked_message(target_path, path))

        rel_path = target_path.relative_to(source_dir)
        target = str(path)
        self.config.add_to_paths(str(rel_path), target)
        self.config.write()

    def add_to_git_ignore(self, pattern: str) -> None:
        source_dir = Config.get_source_directory()
        source_dir.mkdir(parents=True, exist_ok=True)
        gitignore_path = source_dir / ".gitignore"

        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if pattern in content.splitlines():
                return
            gitignore_path.write_text(content + f"\n{pattern}\n")
        else:
            gitignore_path.write_text(f"{pattern}\n")

    def remove_from_git_ignore(self, pattern: str) -> None:
        source_dir = Config.get_source_directory()
        gitignore_path = source_dir / ".gitignore"

        if not gitignore_path.exists():
            raise FileNotFoundError(
                f".gitignore not found at {gitignore_path}")

        lines = gitignore_path.read_text().splitlines()
        new_lines = [line for line in lines if line != pattern]
        gitignore_path.write_text("\n".join(new_lines) + "\n")

    def add_to_no_update(self, pattern: str) -> None:
        if pattern not in self.config.no_update_on:
            self.config.no_update_on.append(pattern)
            self.config.write()

    def remove_from_no_update(self, pattern: str) -> None:
        if pattern in self.config.no_update_on:
            self.config.no_update_on.remove(pattern)
            self.config.write()

    def add_to_no_new_files(self, path: Path) -> None:
        source_dir = Config.get_source_directory()
        try:
            rel_path = path.relative_to(source_dir)
        except ValueError:
            print_err(
                f"{RED}can't add to {GREEN}no_new_files because {BLUE}{
                    path.absolute()
                } is not in {BLUE}{source_dir.absolute()}"
            )
            f"Path {path} is not inside source directory {source_dir}"

        rel_str = str(rel_path)
        if rel_str not in self.config.no_new_files:
            self.config.no_new_files.append(rel_str)
            self.config.write()

    def remove_from_no_new_files(self, path: Path) -> None:
        source_dir = Config.get_source_directory()
        rel_path = path.relative_to(source_dir)
        rel_str = str(rel_path)

        if rel_str in self.config.no_new_files:
            self.config.no_new_files.remove(rel_str)
            self.config.write()

    def set_config_value(self, tag: str, setting: str, *values) -> None:
        self.config.update(tag, setting, *values)
        self.config.write()

    def dsym(self, pattern: str) -> None:
        source_dir = Config.get_source_directory()
        abs_paths = self.config.get_absolute_paths()

        matched = False
        for source_rel, target_str in abs_paths.items():
            if fnmatch.fnmatch(source_rel, pattern):
                matched = True
                source_path = source_dir / source_rel
                target_path = Path(target_str)

                if target_path.is_symlink():
                    target_path.unlink()
                elif target_path.exists():
                    print_err(
                        f"{RED}Target {BLUE}{BOLD}{target_path}{
                            RED} exists and is not a symlink, skipping"
                    )
                    continue

                _safe_move_dir(source_path, target_path)
                self.config.remove_from_paths(target_path)
                self.config.write()

                self._cleanup_empty_groups(source_dir, source_rel)

        if matched:
            self.config.write()
        else:
            print_err(
                f"{RED}No matches found for pattern: {
                    BLUE}{BOLD}{pattern}{RESET}"
            )

    def _cleanup_empty_groups(self, source_dir: Path, source_rel: str) -> None:
        rel_path = Path(source_rel)
        if rel_path.parent == Path("."):
            return

        parent = rel_path.parent
        while parent != Path("."):
            group_dir = source_dir / parent
            if group_dir.exists() and not any(group_dir.iterdir()):
                try:
                    group_dir.rmdir()
                    print(f"dsym: removed empty group {
                          BLUE}{BOLD}{group_dir}{RESET}")
                except OSError:
                    break
            else:
                break
            parent = parent.parent
