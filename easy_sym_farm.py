#!/usr/bin/env python3
import sys

import cli
from commands import CommandHandler
from errors import EasySymError, exit_with_error


def main():
    args = sys.argv[1:]
    command, rest = cli.parse_args(args)
    handler = CommandHandler()
    try:
        if command == "help":
            cli.print_help()
        elif command == "link":
            handler.link()
        elif command == "unlink":
            pattern = rest[0] if rest else None
            handler.unlink(pattern)
        elif command == "push":
            handler.push()
        elif command == "add":
            handler.add(rest)
        elif command == "add-to-git-ignore":
            handler.add_to_git_ignore(rest[0])
        elif command == "remove-from-git-ignore":
            handler.remove_from_git_ignore(rest[0])
        elif command == "add-to-no-update":
            handler.add_to_no_update(rest[0])
        elif command == "remove-from-no-update":
            handler.remove_from_no_update(rest[0])
        elif command == "add-to-no-new-files":
            handler.add_to_no_new_files(rest[0])
        elif command == "remove-from-no-new-files":
            handler.remove_from_no_new_files(rest[0])
        elif command == "add-to-no-sym":
            handler.add_to_no_sym(rest[0])
        elif command == "remove-from-no-sym":
            handler.remove_from_no_sym(rest[0])
        elif command == "set":
            handle_set(handler, rest)
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            cli.print_help()
            sys.exit(1)
    except EasySymError as e:
        exit_with_error(e)


def handle_set(handler: CommandHandler, rest: list):
    if len(rest) < 2:
        print("set requires at least 2 arguments", file=sys.stderr)
        sys.exit(1)
    subcommand = rest[0]
    if subcommand == "source":
        handler.set_source(rest[1])
    elif subcommand == "meta-name":
        handler.set_meta_name(rest[1])
    elif len(rest) >= 3:
        handler.set_config_value(rest[0], rest[1], " ".join(rest[2:]))
    else:
        print(f"Unknown set command: {subcommand}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
