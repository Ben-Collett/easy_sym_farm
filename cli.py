import sys
from pathlib import Path
from commands import CommandProcessor
from config import Config

from ansii import GREEN, BLUE, RESET, BOLD


class Parser:
    def __init__(self):
        self.config = Config.load()
        self.processor = CommandProcessor(self.config)

    def dispatch(self, *argv) -> None:
        args = list(argv)
        if not args or args[0] in ("-h", "--help", "help"):
            self.print_help()
            return

        command = args[0]
        rest = args[1:]

        if command == "link":
            self.processor.link_all()
        elif command == "unlink":
            if rest:
                self.processor.unlink_source_match_pattern(rest[0])
            else:
                self.processor.unlink_all()
        elif command == "push":
            self.processor.push()
        elif command == "add":
            if not rest:
                print("Error: 'add' requires at least one argument", file=sys.stderr)
                sys.exit(1)
            path = Path(rest[0])
            if len(rest) >= 2:
                group = rest[1]
                self.processor.add_path_and_group(path, group)
            else:
                self.processor.add(path)
        elif command == "add-to-git-ignore":
            if not rest:
                print("Error: 'add-to-git-ignore' requires a pattern", file=sys.stderr)
                sys.exit(1)
            self.processor.add_to_git_ignore(rest[0])
        elif command == "remove-from-git-ignore":
            if not rest:
                print(
                    "Error: 'remove-from-git-ignore' requires a pattern",
                    file=sys.stderr,
                )
                sys.exit(1)
            self.processor.remove_from_git_ignore(rest[0])
        elif command == "add-to-no-update":
            if not rest:
                print("Error: 'add-to-no-update' requires a pattern", file=sys.stderr)
                sys.exit(1)
            self.processor.add_to_no_update(rest[0])
        elif command == "remove-from-no-update":
            if not rest:
                print(
                    "Error: 'remove-from-no-update' requires a pattern", file=sys.stderr
                )
                sys.exit(1)
            self.processor.remove_from_no_update(rest[0])
        elif command == "add-to-no-new-files":
            if not rest:
                print("Error: 'add-to-no-new-files' requires a path", file=sys.stderr)
                sys.exit(1)
            self.processor.add_to_no_new_files(Path(rest[0]))
        elif command == "remove-from-no-new-files":
            if not rest:
                print(
                    "Error: 'remove-from-no-new-files' requires a path", file=sys.stderr
                )
                sys.exit(1)
            self.processor.remove_from_no_new_files(Path(rest[0]))
        elif command == "set":
            if len(rest) < 2:
                print(
                    "Error: 'set' requires at least a tag and setting", file=sys.stderr
                )
                sys.exit(1)
            tag = rest[0]
            setting = rest[1]
            values = rest[2:] if len(rest) > 2 else []
            self.processor.set_config_value(tag, setting, *values)
        elif command == "dsym":
            if not rest:
                print("Error: 'dsym' requires a pattern", file=sys.stderr)
                sys.exit(1)
            self.processor.dsym(rest[0])
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            self.print_help()
            sys.exit(1)

    def print_help(self) -> None:
        print(f"""{BOLD}Easy Sym Farm{RESET} - Manage symbolic links to your configuration files

{BOLD}Flags:{RESET}
    {BLUE}-h{RESET} -> Print all available flags, what they do and a brief program description

{BOLD}Subcommands:{RESET}
    {GREEN}help{RESET} -> Print all available flags, what they do and a brief program description
    {GREEN}link{RESET} -> Symlink the files in the source directory
    {GREEN}unlink{RESET} -> Unlinks all symlinked files from the source directory
    {GREEN}unlink <pattern>{RESET} -> Unlinks all files relative to the source directory root using the file pattern
    {GREEN}desym <pattern>{RESET} -> Removes the symlink from the file and moves it back to it's proper location
    {GREEN}push{RESET} -> Uses git add, commit, push to push the changes
    {GREEN}add <file>{RESET} -> Add a non-symlink file or directory, move it to source, and link it
    {GREEN}add <file> <group>{RESET} -> Add a file to a group directory in the source
    {GREEN}add-to-git-ignore <pattern>{RESET} -> Adds a pattern to the .gitignore file
    {GREEN}remove-from-git-ignore <pattern>{RESET} -> Removes a pattern from the .gitignore file
    {GREEN}add-to-no-update <pattern>{RESET} -> Adds a file pattern to the no-update-on list
    {GREEN}remove-from-no-update <pattern>{RESET} -> Removes a file pattern from the no-update-on list
    {GREEN}add-to-no-new-files <path>{RESET} -> Adds a path to the no-new-files list
    {GREEN}remove-from-no-new-files <path>{RESET} -> Removes a path from the no-new-files list
    {GREEN}set <tag> <setting> <value(s)>{RESET} -> Set any value from the config
    {GREEN}dsym <pattern>{RESET} -> Dematerialize symlink: removes symlink, copies file to target, removes from paths
""")


if __name__ == "__main__":
    parser = Parser()
    parser.dispatch(*sys.argv[1:])
