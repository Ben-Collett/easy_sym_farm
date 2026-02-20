import sys
from typing import List, Optional

HELP_TEXT = """easy_sym_farm - A symlink farm manager

Usage: easy_env_sym <command> [arguments]

Commands:
  help, -h                    Show this help message
  link                        Create symlinks from source to target
  unlink [pattern]            Remove symlinks (optionally matching pattern)
  push                        Git add, commit, and push changes
  add <path>                  Move file/dir to source and link it
  add <rel_path> <abs_path>   Add with custom source path (adds to path_overrides)
  add-to-git-ignore <pattern>     Add pattern to .gitignore
  remove-from-git-ignore <pattern> Remove pattern from .gitignore
  add-to-no-update <pattern>      Add pattern to no-update-on list
  remove-from-no-update <pattern> Remove pattern from no-update-on list
  add-to-no-new-files <path>      Add path to no-new-files list
  remove-from-no-new-files <path> Remove path from no-new-files list
  add-to-no-sym <pattern>         Add pattern to no-sym list
  remove-from-no-sym <pattern>    Remove pattern from no-sym list
  set source <path>               Set source directory
  set meta-name <name>            Set metadata file name
  set <tag> <setting> <value>     Set any config value

Environment Variables:
  $easy_sym_source       Source directory (default: ~/easy_syms)
  $easy_sym_meta_name    Metadata filename (default: easy_env_sym_data.toml)
"""


def print_help():
    print(HELP_TEXT)


def parse_args(args: List[str]) -> tuple:
    if not args or args[0] in ["-h", "help"]:
        return ("help", [])

    command = args[0]
    rest = args[1:]
    return (command, rest)


def validate_path_exists(path: str) -> bool:
    import os

    return os.path.exists(path)
