# Easy Sym Farm

Easy Sym Farm is a symlink farm written in Python, similar to stow. It allows you to manage symbolic links to your configuration files and easily back them up to external platforms like GitHub.

## Installation

Install using dumbinstaller:

Install [dumb_installer](https://github.com/Ben-Collett/dumb_installer) first, then run:

```bash
din Ben-Collett/easy_sym_farm
```

Without installing:

```bash
git clone https://github.com/Ben-Collett/easy_sym_farm
cd easy_sym_farm
python easy_sym_farm.py
```

## Environment Variables

- `$easy_sym_source` - The directory where all files that need to be symlinked live. Defaults to `$HOME/easy_syms`.
- `$easy_sym_meta_name` - The name of the metadata file. Defaults to `easy_env_sym_data.toml`.

## CLI Commands

| Command | Description |
|---------|-------------|
| `link` | Symlink the files in the source directory |
| `unlink` | Unlinks all symlinked files from the source directory |
| `unlink <pattern>` | Unlinks all files relative to the source directory root using the file pattern |
| `push` | Uses git add, commit, push to push the changes |
| `add <file>` | Add a non-symlink file or directory, move it to source, and link it |
| `add <file> <group>` | Add a file to a group directory in the source |
| `add-to-git-ignore <pattern>` | Adds a pattern to the .gitignore file |
| `remove-from-git-ignore <pattern>` | Removes a pattern from the .gitignore file |
| `add-to-no-update <pattern>` | Adds a file pattern to the no-update-on list |
| `remove-from-no-update <pattern>` | Removes a file pattern from the no-update-on list |
| `add-to-no-new-files <path>` | Adds a path to the no-new-files list |
| `remove-from-no-new-files <path>` | Removes a path from the no-new-files list |
| `set <tag> <setting> <value(s)>` | Set any value from the config |
| `dsym <pattern>` | Dematerialize symlink: removes symlink, copies file to target, removes from paths |

## Configuration Options

The configuration is stored in a TOML file (default: `easy_env_sym_data.toml`) in the source directory.

### `[general]` Tag

| Setting | Type | Description |
|---------|------|-------------|
| `no-new-files` | list[str] | Paths to directories where new files shouldn't be created, deleted, or renamed. Files within can still be modified. Used to prevent accidentally committing secrets. |
| `no-update-on` | list[str] | File patterns. If after running git status all changed files match these patterns, they should not be git added/committed/pushed. Useful for files like lock files that don't need to be backed up every time. |
| `push-notify-command` | Optional[str] | Command to run when push succeeds or fails. The string `$!SYM_MESSAGE` in the command will be substituted with the actual message. |

### `[network]` Tag

| Setting | Type | Description |
|---------|------|-------------|
| `retry-delays-ms` | int | Delay in milliseconds between retry attempts. Default: 6000 |
| `max-attempts` | int | Maximum number of retry attempts for push operations. Default: 10 |

### `[paths]` Tag

| Setting | Type | Description |
|---------|------|-------------|
| `<source_path>` | str | Maps a relative path from the source directory to an absolute target path. For example: `"editors/tuis/nvim" = "~/.config/nvim"` |

## Contributions

Contributions are welcome! Please feel free to open issues or submit pull requests.

## About abandoned_spec.md and abandoned_specs/

This project was originally created using spec-driven development (SDD). The idea was to write a detailed specification first, then have an AI implement it. This approach didn't work out well - the specifications became too complex and the implementation diverged from them. The `abandoned_spec.md` file contains the original specification that was eventually abandoned.

The `abandoned_specs/` directory was an attempt at contract-driven development using LLMs, where the idea was to have AI generate both a specification and a corresponding implementation that would be verified against each other. This also didn't work out.

Both approaches were abandoned in favor of direct implementation but are left because I plan on creating notes on my attempts and issues I encountered with each approach.

## License

BSD Zero Clause License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Benjamin Collett
