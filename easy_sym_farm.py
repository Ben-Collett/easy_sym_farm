#!/usr/bin/env python3
"""
easy_sym_farm - A symlink farm manager similar to GNU Stow

This project was created using AI spec-driven development.
"""

import os
import sys
import argparse
import fnmatch
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Try to import tomllib for Python 3.11+, otherwise use a minimal TOML parser
HAS_TOMLLIB = False
tomllib: Any = None
try:
    import tomllib

    HAS_TOMLLIB = True
except ImportError:
    pass


# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_FAILURE = 1
EXIT_GIT_NOT_INSTALLED = 2
EXIT_NOT_GIT_REPO = 3
EXIT_NO_REMOTE_ORIGIN = 4


def get_home_directory() -> str:
    """Get the home directory, respecting SUDO_USER if present."""
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        import pwd

        return pwd.getpwnam(sudo_user).pw_dir
    return os.path.expanduser("~")


def get_source_directory() -> Path:
    """Get the source directory from environment or default."""
    env_source = os.environ.get("easy_sym_source")
    if env_source:
        return Path(env_source).expanduser().resolve()
    return Path(get_home_directory()) / "easy_syms"


def get_meta_file_name() -> str:
    """Get the metadata file name from environment or default."""
    return os.environ.get("easy_sym_meta_name", "easy_env_sym_data.toml")


class SimpleTOMLParser:
    """Minimal TOML parser for configuration files."""

    @staticmethod
    def parse(content: str) -> Dict[str, Any]:
        """Parse TOML content into a dictionary."""
        result: Dict[str, Any] = {}
        current_section = None
        current_table = result

        for line in content.split("\n"):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Handle section headers
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()

                # Handle nested tables like [path_overrides]
                if "." in section_name:
                    parts = section_name.split(".")
                    current_table = result
                    for part in parts:
                        if part not in current_table:
                            current_table[part] = {}
                        current_table = current_table[part]
                else:
                    if section_name not in result:
                        result[section_name] = {}
                    current_table = result[section_name]
                continue

            # Handle key-value pairs
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Strip quotes from key if present
                if (key.startswith('"') and key.endswith('"')) or (
                    key.startswith("'") and key.endswith("'")
                ):
                    key = key[1:-1]

                # Parse value
                parsed_value = SimpleTOMLParser._parse_value(value)
                current_table[key] = parsed_value

        return result

    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse a TOML value."""
        value = value.strip()

        # Array
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                return []
            items = []
            current = ""
            in_string = False
            string_char = None

            for char in inner:
                if not in_string and char in "\"'":
                    in_string = True
                    string_char = char
                    continue
                elif in_string and char == string_char:
                    in_string = False
                    string_char = None
                    continue
                elif not in_string and char == ",":
                    if current.strip():
                        items.append(SimpleTOMLParser._parse_value(current.strip()))
                    current = ""
                    continue
                current += char

            if current.strip():
                items.append(SimpleTOMLParser._parse_value(current.strip()))
            return items

        # String
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        return value

    @staticmethod
    def dump(data: Dict[str, Any]) -> str:
        """Dump dictionary to TOML format."""
        lines = []

        # First, handle top-level keys
        for key, value in data.items():
            if not isinstance(value, dict):
                lines.append(SimpleTOMLParser._format_key_value(key, value))

        # Then handle sections
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"\n[{key}]")
                for sub_key, sub_value in value.items():
                    lines.append(SimpleTOMLParser._format_key_value(sub_key, sub_value))

        return "\n".join(lines)

    @staticmethod
    def _format_key_value(key: str, value: Any) -> str:
        """Format a key-value pair for TOML."""
        if isinstance(value, list):
            if not value:
                return f"{key} = []"
            items = []
            for item in value:
                if isinstance(item, str):
                    items.append(f'"{item}"')
                else:
                    items.append(str(item))
            return f"{key} = [{', '.join(items)}]"
        elif isinstance(value, str):
            return f'{key} = "{value}"'
        elif isinstance(value, bool):
            return f"{key} = {str(value).lower()}"
        else:
            return f"{key} = {value}"


def load_config(source_dir: Path) -> Dict[str, Any]:
    """Load configuration from the metadata file."""
    meta_file = source_dir / get_meta_file_name()

    if not meta_file.exists():
        return _default_config()

    content = meta_file.read_text()

    if HAS_TOMLLIB:
        try:
            return tomllib.loads(content)
        except Exception:
            return _default_config()
    else:
        try:
            return SimpleTOMLParser.parse(content)
        except Exception:
            return _default_config()


def _default_config() -> Dict[str, Any]:
    """Return default configuration."""
    return {
        "general": {
            "output_root_target": get_home_directory(),
            "no-new-files": [],
            "no-sym": [],
            "no-update-on": [],
            "push-notify-command": None,
        },
        "network": {
            "retry-delay-ms": 6000,
            "max-attempts": 10,
        },
        "path_overrides": {},
    }


def save_config(source_dir: Path, config: Dict[str, Any]) -> None:
    """Save configuration to the metadata file."""
    meta_file = source_dir / get_meta_file_name()
    source_dir.mkdir(parents=True, exist_ok=True)

    content = SimpleTOMLParser.dump(config)
    meta_file.write_text(content)


def matches_pattern(path: str, pattern: str) -> bool:
    """Check if a path matches a glob pattern."""
    # Handle directory patterns that should match recursively
    if pattern.endswith("/") or pattern.endswith("/*"):
        base_pattern = pattern.rstrip("/*")
        return (
            fnmatch.fnmatch(path, base_pattern)
            or path.startswith(base_pattern + "/")
            or path == base_pattern
        )

    return fnmatch.fnmatch(path, pattern)


def should_exclude(
    rel_path: str, no_sym_patterns: List[str], default_exclusions: List[str]
) -> bool:
    """Check if a path should be excluded based on no-sym patterns and defaults."""
    # Check default exclusions
    for exclusion in default_exclusions:
        if matches_pattern(rel_path, exclusion):
            return True
        # Check if any parent directory matches
        parts = rel_path.split("/")
        for i in range(1, len(parts)):
            parent = "/".join(parts[:i])
            if matches_pattern(parent, exclusion):
                return True

    # Check no-sym patterns
    for pattern in no_sym_patterns:
        if matches_pattern(rel_path, pattern):
            return True
        # Check if any parent directory matches
        parts = rel_path.split("/")
        for i in range(1, len(parts)):
            parent = "/".join(parts[:i])
            if matches_pattern(parent, pattern):
                return True

    return False


def get_default_exclusions(source_dir: Path) -> List[str]:
    """Get the list of default exclusions."""
    meta_file = get_meta_file_name()
    return [".git", ".gitignore", meta_file]


def get_managed_files(source_dir: Path, no_sym_patterns: List[str]) -> List[Path]:
    """Get list of all managed files in sorted order."""
    default_exclusions = get_default_exclusions(source_dir)
    managed = []

    if not source_dir.exists():
        return managed

    for root, dirs, files in os.walk(source_dir):
        # Sort directories for deterministic traversal
        dirs.sort()

        rel_root = Path(root).relative_to(source_dir)
        if str(rel_root) == ".":
            rel_root = ""

        # Check each directory
        for d in dirs[:]:
            rel_path = str(Path(str(rel_root)) / d) if rel_root else d
            if should_exclude(rel_path, no_sym_patterns, default_exclusions):
                dirs.remove(d)  # Don't traverse into excluded directories
                managed.append(Path(root) / d)
            elif not should_exclude(rel_path, [], default_exclusions):
                managed.append(Path(root) / d)

        # Check each file
        for f in sorted(files):
            rel_path = str(Path(str(rel_root)) / f) if rel_root else f
            if not should_exclude(rel_path, no_sym_patterns, default_exclusions):
                managed.append(Path(root) / f)

    # Sort by relative path for deterministic order
    managed.sort(
        key=lambda p: (
            str(p.relative_to(source_dir)) if p.is_relative_to(source_dir) else str(p)
        )
    )
    return managed


def get_destination_path(
    source_path: Path,
    source_dir: Path,
    output_root: Path,
    path_overrides: Dict[str, str],
) -> Path:
    """Calculate the destination path for a source file."""
    rel_path = source_path.relative_to(source_dir)
    rel_str = str(rel_path)

    # Check for path overrides
    for pattern, override in path_overrides.items():
        if matches_pattern(rel_str, pattern):
            # If pattern matches a directory, use the override for the whole path
            if pattern.endswith("/") or pattern.endswith("/*"):
                base = pattern.rstrip("/*")
                remaining = rel_str[len(base) :].lstrip("/")
                return Path(override) / remaining if remaining else Path(override)
            else:
                return Path(override)

    # Default: relative to output root
    return output_root / rel_path


def error_exit(message: str, exit_code: int = EXIT_GENERAL_FAILURE) -> None:
    """Print error message to stderr and exit."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def run_notify_command(command: Optional[str], message: str) -> None:
    """Run the notify command with the given message."""
    if command and "$!SYM_MESSAGE" in command:
        full_command = command.replace("$!SYM_MESSAGE", f'"{message}"')
        try:
            subprocess.run(full_command, shell=True, check=False)
        except Exception:
            pass


def cmd_link(args: argparse.Namespace) -> int:
    """Link files from source directory to output root."""
    source_dir = get_source_directory()
    config = load_config(source_dir)

    general = config.get("general", {})
    output_root_str = general.get("output_root_target", get_home_directory())
    output_root = Path(str(output_root_str)).expanduser().resolve()
    no_sym_patterns = general.get("no-sym", [])
    path_overrides = config.get("path_overrides", {})

    # Ensure source directory exists
    source_dir.mkdir(parents=True, exist_ok=True)

    # Track linked paths for ancestor/descendant checking
    linked_paths: Dict[Path, Path] = {}  # destination -> source
    successful: List[Path] = []
    failed: List[Tuple[Path, str]] = []

    # Get all managed files (sorted for deterministic order)
    managed_files = get_managed_files(source_dir, no_sym_patterns)

    # Filter to only top-level entries (we link directories as units)
    top_level = [
        f
        for f in managed_files
        if f.parent == source_dir
        or (f.parent.parent == source_dir and f.parent.name == "")
    ]

    # Actually, let's link everything, but handle ancestor/descendant conflicts
    for source_path in managed_files:
        rel_path = source_path.relative_to(source_dir)

        # Skip if excluded
        if should_exclude(
            str(rel_path), no_sym_patterns, get_default_exclusions(source_dir)
        ):
            continue

        dest_path = get_destination_path(
            source_path, source_dir, output_root, path_overrides
        )

        # Check if we need root privileges for this path
        try:
            dest_parent = dest_path.parent
            if not dest_parent.exists():
                dest_parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            error_exit(
                f"Permission denied creating {dest_path}. Try running with sudo.",
                EXIT_GENERAL_FAILURE,
            )

        # Check for ancestor/descendant conflicts
        ancestor_conflict = False
        for linked_dest, linked_src in list(linked_paths.items()):
            # Check if current is ancestor of already linked
            try:
                if str(dest_path) in str(linked_dest) or str(linked_dest) in str(
                    dest_path
                ):
                    # One is ancestor of the other
                    if dest_path in linked_dest.parents or dest_path == linked_dest:
                        # Current is ancestor of linked - unlink the linked one
                        try:
                            if linked_dest.is_symlink():
                                linked_dest.unlink()
                                # Remove empty parent directories
                                parent = linked_dest.parent
                                while parent != output_root and parent.exists():
                                    try:
                                        parent.rmdir()  # Only removes if empty
                                        parent = parent.parent
                                    except OSError:
                                        break
                            del linked_paths[linked_dest]
                            successful = [s for s in successful if s != linked_src]
                        except Exception as e:
                            failed.append((linked_src, str(e)))
                    elif linked_dest in dest_path.parents or linked_dest == dest_path:
                        # Linked is ancestor of current - skip current
                        ancestor_conflict = True
                        break
            except ValueError:
                # Different paths, no relation
                pass

        if ancestor_conflict:
            continue

        # Check destination
        if dest_path.exists() or dest_path.is_symlink():
            if dest_path.is_symlink():
                current_target = os.readlink(dest_path)
                if Path(current_target) == source_path:
                    # Already correctly linked
                    linked_paths[dest_path] = source_path
                    continue
                else:
                    failed.append(
                        (
                            source_path,
                            f"Symlink exists at {dest_path} pointing elsewhere",
                        )
                    )
                    continue
            else:
                failed.append((source_path, f"Regular file exists at {dest_path}"))
                continue

        # Create symlink
        try:
            dest_path.symlink_to(source_path)
            linked_paths[dest_path] = source_path
            successful.append(source_path)
        except Exception as e:
            failed.append((source_path, str(e)))

    # Print summary
    if successful:
        print(f"Successfully linked {len(successful)} items")
    if failed:
        print(f"Failed to link {len(failed)} items:", file=sys.stderr)
        for path, reason in failed:
            print(f"  {path}: {reason}", file=sys.stderr)
        return EXIT_GENERAL_FAILURE

    return EXIT_SUCCESS


def cmd_unlink(args: argparse.Namespace) -> int:
    """Unlink symlinks created by this program."""
    source_dir = get_source_directory()
    config = load_config(source_dir)

    general = config.get("general", {})
    output_root_str = general.get("output_root_target", get_home_directory())
    output_root = Path(str(output_root_str)).expanduser().resolve()
    no_sym_patterns = general.get("no-sym", [])
    pattern: Optional[str] = args.pattern if hasattr(args, "pattern") else None

    unlinked = 0
    errors = []

    # Get all managed files
    managed_files = get_managed_files(source_dir, no_sym_patterns)
    path_overrides = config.get("path_overrides", {})

    for source_path in managed_files:
        rel_path = source_path.relative_to(source_dir)

        # If pattern specified, check match
        if pattern and not matches_pattern(str(rel_path), pattern):
            continue

        dest_path = get_destination_path(
            source_path, source_dir, output_root, path_overrides
        )

        if dest_path.is_symlink():
            try:
                target = os.readlink(dest_path)
                # Only unlink if it points to our source directory
                if Path(target).is_relative_to(source_dir):
                    dest_path.unlink()
                    unlinked += 1

                    # Remove empty parent directories
                    parent = dest_path.parent
                    while parent != output_root and parent.exists():
                        try:
                            parent.rmdir()
                            parent = parent.parent
                        except OSError:
                            break
            except Exception as e:
                errors.append((dest_path, str(e)))

    if errors:
        print(f"Errors during unlink:", file=sys.stderr)
        for path, reason in errors:
            print(f"  {path}: {reason}", file=sys.stderr)

    print(f"Unlinked {unlinked} items")
    return EXIT_SUCCESS if not errors else EXIT_GENERAL_FAILURE


def cmd_push(args: argparse.Namespace) -> int:
    """Push changes to git remote."""
    source_dir = get_source_directory()

    # Check if git is installed
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        error_exit("Git is not installed", EXIT_GIT_NOT_INSTALLED)

    # Check if we're in a git repo
    try:
        result = subprocess.run(
            ["git", "-C", str(source_dir), "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            error_exit("Not a git repository", EXIT_NOT_GIT_REPO)
    except Exception:
        error_exit("Not a git repository", EXIT_NOT_GIT_REPO)

    # Check for remote origin
    try:
        result = subprocess.run(
            ["git", "-C", str(source_dir), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            error_exit("No remote origin found", EXIT_NO_REMOTE_ORIGIN)
    except Exception:
        error_exit("No remote origin found", EXIT_NO_REMOTE_ORIGIN)

    config = load_config(source_dir)
    general = config.get("general", {})
    network = config.get("network", {})
    no_new_files = general.get("no-new-files", [])
    no_update_on = general.get("no-update-on", [])
    notify_command: Optional[str] = general.get("push-notify-command")
    max_attempts = network.get("max-attempts", 10)
    retry_delay_ms = network.get("retry-delay-ms", 6000)

    # Get git status
    result = subprocess.run(
        ["git", "-C", str(source_dir), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        error_exit("Failed to get git status", EXIT_GENERAL_FAILURE)

    lines = [l for l in result.stdout.strip().split("\n") if l.strip()]

    if not lines:
        print("No changes to push")
        return EXIT_SUCCESS

    # Check no-new-files restrictions
    for line in lines:
        if len(line) < 3:
            continue
        status = line[:2]
        file_path = line[3:].strip()

        # Check for new files ('??') or deleted files (' D', 'D ')
        if status == "??" or "D" in status:
            for restricted in no_new_files:
                if file_path.startswith(restricted) or matches_pattern(
                    file_path, restricted
                ):
                    error_exit(
                        f"New/deleted file in restricted path: {file_path}",
                        EXIT_GENERAL_FAILURE,
                    )

    # Check if all changes match no-update-on patterns
    all_match_no_update = True
    for line in lines:
        if len(line) < 3:
            continue
        file_path = line[3:].strip()

        matches_any = False
        for pattern in no_update_on:
            if matches_pattern(file_path, pattern):
                matches_any = True
                break

        if not matches_any:
            all_match_no_update = False
            break

    if all_match_no_update and no_update_on:
        print("All changes match no-update-on patterns, skipping push")
        return EXIT_SUCCESS

    # Stage all changes
    result = subprocess.run(
        ["git", "-C", str(source_dir), "add", "."], capture_output=True
    )
    if result.returncode != 0:
        error_exit("Failed to stage changes", EXIT_GENERAL_FAILURE)

    # Create commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = subprocess.run(
        ["git", "-C", str(source_dir), "commit", "-m", timestamp], capture_output=True
    )

    if result.returncode != 0:
        # Check if it's because there's nothing to commit
        if (
            b"nothing to commit" in result.stdout
            or b"nothing to commit" in result.stderr
        ):
            print("Nothing to commit")
            return EXIT_SUCCESS
        error_exit("Failed to create commit", EXIT_GENERAL_FAILURE)

    # Push with retry logic
    last_error = None
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            ["git", "-C", str(source_dir), "push"], capture_output=True, text=True
        )

        if result.returncode == 0:
            message = "Successfully pushed changes"
            print(message)
            if notify_command:
                run_notify_command(notify_command, message)
            return EXIT_SUCCESS

        # Check if it's a network error
        stderr_lower = result.stderr.lower()
        is_network_error = any(
            phrase in stderr_lower
            for phrase in [
                "could not resolve host",
                "connection timed out",
                "failed to connect",
            ]
        )

        if is_network_error and attempt < max_attempts:
            print(
                f"Network error on attempt {attempt}, retrying in {retry_delay_ms}ms..."
            )
            import time

            time.sleep(retry_delay_ms / 1000)
            last_error = result.stderr
        else:
            break

    # Push failed
    message = f"Push failed: {last_error or result.stderr}"
    print(message, file=sys.stderr)
    if notify_command:
        run_notify_command(notify_command, message)
    return EXIT_GENERAL_FAILURE


def cmd_add(args: argparse.Namespace) -> int:
    """Add a file/directory to the source directory and create symlink."""
    source_dir = get_source_directory()
    config = load_config(source_dir)

    general = config.get("general", {})
    output_root_str = general.get("output_root_target", get_home_directory())
    output_root = Path(str(output_root_str)).expanduser().resolve()

    paths: List[str] = args.paths if hasattr(args, "paths") else []

    if len(paths) == 1:
        # Single path variant - must be under output_root
        src_path = Path(paths[0]).expanduser().resolve()

        try:
            src_path.relative_to(output_root)
        except ValueError:
            error_exit(
                f"Path {src_path} is not under {output_root}", EXIT_GENERAL_FAILURE
            )

        # Calculate relative path from output_root
        rel_path = src_path.relative_to(output_root)
        dest_in_source = source_dir / rel_path

        # Move to source directory
        source_dir.mkdir(parents=True, exist_ok=True)
        dest_in_source.parent.mkdir(parents=True, exist_ok=True)

        if dest_in_source.exists():
            error_exit(
                f"Destination already exists in source: {dest_in_source}",
                EXIT_GENERAL_FAILURE,
            )

        try:
            shutil.move(str(src_path), str(dest_in_source))
        except Exception as e:
            error_exit(f"Failed to move {src_path}: {e}", EXIT_GENERAL_FAILURE)

        # Create symlink
        try:
            src_path.symlink_to(dest_in_source)
            print(f"Added {rel_path} to source directory")
        except Exception as e:
            # Try to move back
            try:
                shutil.move(str(dest_in_source), str(src_path))
            except:
                pass
            error_exit(f"Failed to create symlink: {e}", EXIT_GENERAL_FAILURE)

    elif len(paths) == 2:
        # Two path variant - add to path_overrides
        rel_in_source = paths[0]
        target_path = Path(paths[1]).expanduser().resolve()

        if not target_path.exists():
            error_exit(
                f"Target path does not exist: {target_path}", EXIT_GENERAL_FAILURE
            )

        # Add to path_overrides
        if "path_overrides" not in config:
            config["path_overrides"] = {}

        config["path_overrides"][rel_in_source] = str(target_path)
        save_config(source_dir, config)

        # Now run link to create the symlink
        return cmd_link(args)

    else:
        error_exit("Invalid number of arguments for add command", EXIT_GENERAL_FAILURE)

    return EXIT_SUCCESS


def cmd_gitignore(args: argparse.Namespace) -> int:
    """Add or remove patterns from .gitignore."""
    source_dir = get_source_directory()
    source_dir.mkdir(parents=True, exist_ok=True)

    gitignore_path = source_dir / ".gitignore"

    action = args.action if hasattr(args, "action") else "add"
    pattern: Optional[str] = args.pattern if hasattr(args, "pattern") else None

    if not pattern:
        error_exit("Pattern required", EXIT_GENERAL_FAILURE)

    # Ensure pattern is not None after the check above
    assert pattern is not None

    existing_patterns = []
    if gitignore_path.exists():
        existing_patterns = gitignore_path.read_text().strip().split("\n")
        existing_patterns = [p.strip() for p in existing_patterns if p.strip()]

    if action == "add":
        if pattern not in existing_patterns:
            existing_patterns.append(pattern)
            gitignore_path.write_text("\n".join(existing_patterns) + "\n")
            print(f"Added '{pattern}' to .gitignore")
        else:
            print(f"'{pattern}' already in .gitignore")

    elif action == "remove":
        if pattern in existing_patterns:
            existing_patterns.remove(pattern)
            gitignore_path.write_text("\n".join(existing_patterns) + "\n")
            print(f"Removed '{pattern}' from .gitignore")
        else:
            print(f"'{pattern}' not found in .gitignore")

    return EXIT_SUCCESS


def cmd_no_update(args: argparse.Namespace) -> int:
    """Add or remove patterns from no-update-on list."""
    source_dir = get_source_directory()
    config = load_config(source_dir)

    if "general" not in config:
        config["general"] = {}
    if "no-update-on" not in config["general"]:
        config["general"]["no-update-on"] = []

    action = args.action if hasattr(args, "action") else "add"
    pattern: Optional[str] = args.pattern if hasattr(args, "pattern") else None

    if not pattern:
        error_exit("Pattern required", EXIT_GENERAL_FAILURE)
    assert pattern is not None

    no_update_list = config["general"]["no-update-on"]

    if action == "add":
        if pattern not in no_update_list:
            no_update_list.append(pattern)
            save_config(source_dir, config)
            print(f"Added '{pattern}' to no-update-on")
        else:
            print(f"'{pattern}' already in no-update-on")

    elif action == "remove":
        if pattern in no_update_list:
            no_update_list.remove(pattern)
            save_config(source_dir, config)
            print(f"Removed '{pattern}' from no-update-on")
        else:
            print(f"'{pattern}' not found in no-update-on")

    return EXIT_SUCCESS


def cmd_no_new_files(args: argparse.Namespace) -> int:
    """Add or remove paths from no-new-files list."""
    source_dir = get_source_directory()
    config = load_config(source_dir)

    if "general" not in config:
        config["general"] = {}
    if "no-new-files" not in config["general"]:
        config["general"]["no-new-files"] = []

    action = args.action if hasattr(args, "action") else "add"
    path: Optional[str] = args.path if hasattr(args, "path") else None

    if not path:
        error_exit("Path required", EXIT_GENERAL_FAILURE)
    assert path is not None

    no_new_list = config["general"]["no-new-files"]

    if action == "add":
        if path not in no_new_list:
            no_new_list.append(path)
            save_config(source_dir, config)
            print(f"Added '{path}' to no-new-files")
        else:
            print(f"'{path}' already in no-new-files")

    elif action == "remove":
        if path in no_new_list:
            no_new_list.remove(path)
            save_config(source_dir, config)
            print(f"Removed '{path}' from no-new-files")
        else:
            print(f"'{path}' not found in no-new-files")

    return EXIT_SUCCESS


def cmd_no_sym(args: argparse.Namespace) -> int:
    """Add or remove patterns from no-sym list."""
    source_dir = get_source_directory()
    config = load_config(source_dir)

    if "general" not in config:
        config["general"] = {}
    if "no-sym" not in config["general"]:
        config["general"]["no-sym"] = []

    action = args.action if hasattr(args, "action") else "add"
    pattern: Optional[str] = args.pattern if hasattr(args, "pattern") else None

    if not pattern:
        error_exit("Pattern required", EXIT_GENERAL_FAILURE)
    assert pattern is not None

    no_sym_list = config["general"]["no-sym"]

    if action == "add":
        if pattern not in no_sym_list:
            no_sym_list.append(pattern)
            save_config(source_dir, config)
            print(f"Added '{pattern}' to no-sym")
        else:
            print(f"'{pattern}' already in no-sym")

    elif action == "remove":
        if pattern in no_sym_list:
            no_sym_list.remove(pattern)
            save_config(source_dir, config)
            print(f"Removed '{pattern}' from no-sym")
        else:
            print(f"'{pattern}' not found in no-sym")

    return EXIT_SUCCESS


def cmd_set(args: argparse.Namespace) -> int:
    """Set configuration values."""
    source_dir = get_source_directory()
    config = load_config(source_dir)

    setting: Optional[str] = args.setting if hasattr(args, "setting") else None
    value: Optional[str] = args.value if hasattr(args, "value") else None

    if not setting:
        error_exit("Setting name required", EXIT_GENERAL_FAILURE)

    # Handle environment variable settings
    if setting == "source":
        if not value:
            error_exit("Path required for source", EXIT_GENERAL_FAILURE)
        assert value is not None

        # Run unlink first
        unlink_args = argparse.Namespace()
        unlink_args.pattern = None
        cmd_unlink(unlink_args)

        # Update environment and config
        os.environ["easy_sym_source"] = value
        source_dir = Path(value).expanduser().resolve()
        source_dir.mkdir(parents=True, exist_ok=True)

        # Run link
        return cmd_link(args)

    elif setting == "meta-name":
        if not value:
            error_exit("Name required for meta-name", EXIT_GENERAL_FAILURE)
        assert value is not None
        os.environ["easy_sym_meta_name"] = value
        print(f"Set meta-name to '{value}'")
        return EXIT_SUCCESS

    # Handle config settings (tag.setting format or just setting)
    if setting and "." in setting:
        parts = setting.split(".")
        if len(parts) == 2:
            tag, sub_setting = parts
            if tag not in config:
                config[tag] = {}

            # Parse value (could be int, bool, or string)
            if value:
                if value.lower() == "true":
                    config[tag][sub_setting] = True
                elif value.lower() == "false":
                    config[tag][sub_setting] = False
                elif value.isdigit():
                    config[tag][sub_setting] = int(value)
                else:
                    config[tag][sub_setting] = value

            save_config(source_dir, config)
            print(f"Set {setting} = {value}")
        else:
            error_exit(
                "Invalid setting format. Use 'tag.setting'", EXIT_GENERAL_FAILURE
            )
    else:
        # Direct setting under general
        if "general" not in config:
            config["general"] = {}

        if value:
            if value.lower() == "true":
                config["general"][setting] = True
            elif value.lower() == "false":
                config["general"][setting] = False
            elif value.isdigit():
                config["general"][setting] = int(value)
            else:
                config["general"][setting] = value

        save_config(source_dir, config)
        print(f"Set general.{setting} = {value}")

    return EXIT_SUCCESS


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="easy_sym_farm",
        description="A symlink farm manager similar to GNU Stow. "
        "This project was created using AI spec-driven development.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # link command
    link_parser = subparsers.add_parser(
        "link", help="Symlink files from source directory"
    )
    link_parser.set_defaults(func=cmd_link)

    # unlink command
    unlink_parser = subparsers.add_parser("unlink", help="Unlink symlinks")
    unlink_parser.add_argument(
        "pattern", nargs="?", help="Pattern to match for unlinking"
    )
    unlink_parser.set_defaults(func=cmd_unlink)

    # push command
    push_parser = subparsers.add_parser("push", help="Push changes to git remote")
    push_parser.set_defaults(func=cmd_push)

    # add command
    add_parser = subparsers.add_parser("add", help="Add file/directory to source")
    add_parser.add_argument("paths", nargs="+", help="Path(s) to add")
    add_parser.set_defaults(func=cmd_add)

    # gitignore commands
    gitignore_add = subparsers.add_parser(
        "add-to-git-ignore", help="Add pattern to .gitignore"
    )
    gitignore_add.add_argument("pattern", help="Pattern to add")
    gitignore_add.set_defaults(
        func=lambda args: setattr(args, "action", "add") or cmd_gitignore(args)
    )

    gitignore_remove = subparsers.add_parser(
        "remove-from-git-ignore", help="Remove pattern from .gitignore"
    )
    gitignore_remove.add_argument("pattern", help="Pattern to remove")
    gitignore_remove.set_defaults(
        func=lambda args: setattr(args, "action", "remove") or cmd_gitignore(args)
    )

    # no-update commands
    no_update_add = subparsers.add_parser(
        "add-to-no-update", help="Add pattern to no-update-on"
    )
    no_update_add.add_argument("pattern", help="Pattern to add")
    no_update_add.set_defaults(
        func=lambda args: setattr(args, "action", "add") or cmd_no_update(args)
    )

    no_update_remove = subparsers.add_parser(
        "remove-from-no-update", help="Remove pattern from no-update-on"
    )
    no_update_remove.add_argument("pattern", help="Pattern to remove")
    no_update_remove.set_defaults(
        func=lambda args: setattr(args, "action", "remove") or cmd_no_update(args)
    )

    # no-new-files commands
    no_new_add = subparsers.add_parser(
        "add-to-no-new-files", help="Add path to no-new-files"
    )
    no_new_add.add_argument("path", help="Path to add")
    no_new_add.set_defaults(
        func=lambda args: setattr(args, "action", "add") or cmd_no_new_files(args)
    )

    no_new_remove = subparsers.add_parser(
        "remove-from-no-new-files", help="Remove path from no-new-files"
    )
    no_new_remove.add_argument("path", help="Path to remove")
    no_new_remove.set_defaults(
        func=lambda args: setattr(args, "action", "remove") or cmd_no_new_files(args)
    )

    # no-sym commands
    no_sym_add = subparsers.add_parser("add-to-no-sym", help="Add pattern to no-sym")
    no_sym_add.add_argument("pattern", help="Pattern to add")
    no_sym_add.set_defaults(
        func=lambda args: setattr(args, "action", "add") or cmd_no_sym(args)
    )

    no_sym_remove = subparsers.add_parser(
        "remove-from-no-sym", help="Remove pattern from no-sym"
    )
    no_sym_remove.add_argument("pattern", help="Pattern to remove")
    no_sym_remove.set_defaults(
        func=lambda args: setattr(args, "action", "remove") or cmd_no_sym(args)
    )

    # set command
    set_parser = subparsers.add_parser("set", help="Set configuration values")
    set_parser.add_argument("setting", help="Setting name")
    set_parser.add_argument("value", nargs="?", help="Setting value")
    set_parser.set_defaults(func=cmd_set)

    # help command
    help_parser = subparsers.add_parser("help", help="Show help message")
    help_parser.set_defaults(func=lambda args: parser.print_help() or 0)

    # Parse arguments
    args = parser.parse_args()

    if args.command is None or args.command == "help":
        parser.print_help()
        return EXIT_SUCCESS

    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return EXIT_GENERAL_FAILURE
    except Exception as e:
        error_exit(str(e), EXIT_GENERAL_FAILURE)
        return EXIT_GENERAL_FAILURE  # This line is never reached but satisfies type checker


if __name__ == "__main__":
    sys.exit(main())
