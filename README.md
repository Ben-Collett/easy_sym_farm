# easy_sym_farm

> **Disclaimer:** This code was written using AI spec-driven development.

A symlink farm manager in Python similar to GNU Stow. It allows you to manage files from a source directory and link them to target paths, with easy git-based backup capabilities.

## Installation

### Using dumb_installer (Recommended)

Install [dumb_installer](https://github.com/Ben-Collett/dumb_installer) first, then run:

```bash
din Ben-Collett/easy_sym_farm
```

### Manual Installation

```bash
git clone https://github.com/Ben-Collett/easy_sym_farm
cd easy_sym_farm
python easy_sym_farm.py help
```

## Commands

| Command | Description |
|---------|-------------|
| `help`, `-h` | Show help message |
| `link` | Symlink files from source directory |
| `unlink [pattern]` | Unlink symlinked files |
| `push` | Git add, commit, and push changes |
| `add <path> [group_dir]` | Add file/dir to source and link it |
| `add-to-git-ignore <pattern>` | Add pattern to .gitignore |
| `remove-from-git-ignore <pattern>` | Remove pattern from .gitignore |
| `add-to-no-update <pattern>` | Add pattern to no-update-on list |
| `remove-from-no-update <pattern>` | Remove pattern from no-update-on list |
| `add-to-no-new-files <path>` | Add path to no-new-files list |
| `remove-from-no-new-files <path>` | Remove path from no-new-files list |
| `set source <path>` | Set source directory path |
| `set meta-name <name>` | Set metadata file name |
| `set <tag> <setting> <value>` | Set any config value |

## Configuration

### Environment Variables

- `easy_sym_source`: Source directory (default: `~/easy_syms`)
- `easy_sym_meta_name`: Metadata file name (default: `easy_env_sym_data.toml`)

### Metadata File (TOML)

Located in the source directory:

```toml
[general]
no-new-files = ["fish"]           # Directories where new files can't be added
no-update-on = ["nvim/lazy-lock.json"]  # Patterns to skip during push
push-notify-command = "notify -t 100000 $!SYM_MESSAGE"  # Notification command

[network]
retry-delay-ms = 6000             # Delay between retry attempts
max-attempts = 10                 # Max push retry attempts

[paths]
"nvim" = "~/.config/nvim"         # Relative path -> target path mapping
"keyd" = "/etc/keyd"
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 2 | Git not installed |
| 3 | Not a git repository |
| 4 | No remote origin |

## Contribution Guidelines

This project doesn't accept pull requests. It is primarily for experimenting with AI spec-driven development. Feel free to open issues for bugs or suggestions for spec improvements.

## License

[BSD Zero Clause License](LICENSE)
