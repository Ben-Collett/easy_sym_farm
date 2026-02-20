# easy_sym_farm

> **Disclaimer:** This code was written using AI spec-driven development.

A symlink farm manager in Python similar to GNU Stow. It allows you to manage files from a source directory and symlink them to a target directory, with easy git backup integration.

## Installation

### Using dumb_installer (Recommended)

1. Install dumb_installer from [https://github.com/Ben-Collett/dumb_installer](https://github.com/Ben-Collett/dumb_installer)
2. Run:
```bash
din Ben-Collett/easy_sym_farm
```

### Manual Installation

```bash
git clone https://github.com/Ben-Collett/easy_sym_farm
python easy_sym_farm.py
```

## Usage

```
easy_env_sym <command> [arguments]
```

### Commands

| Command | Description |
|---------|-------------|
| `help`, `-h` | Show help message |
| `link` | Create symlinks from source to target |
| `unlink [pattern]` | Remove symlinks (optionally matching pattern) |
| `push` | Git add, commit, and push changes |
| `add <path>` | Move file/dir to source and link it |
| `add <rel_path> <abs_path>` | Add with custom source path (adds to path_overrides) |
| `add-to-git-ignore <pattern>` | Add pattern to .gitignore |
| `remove-from-git-ignore <pattern>` | Remove pattern from .gitignore |
| `add-to-no-update <pattern>` | Add pattern to no-update-on list |
| `remove-from-no-update <pattern>` | Remove pattern from no-update-on list |
| `add-to-no-new-files <path>` | Add path to no-new-files list |
| `remove-from-no-new-files <path>` | Remove path from no-new-files list |
| `add-to-no-sym <pattern>` | Add pattern to no-sym list |
| `remove-from-no-sym <pattern>` | Remove pattern from no-sym list |
| `set source <path>` | Set source directory |
| `set meta-name <name>` | Set metadata file name |
| `set <tag> <setting> <value>` | Set any config value |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `$easy_sym_source` | `~/easy_syms` | Source directory containing managed files |
| `$easy_sym_meta_name` | `easy_env_sym_data.toml` | Metadata filename |

### Configuration (TOML)

The metadata file contains the following sections:

#### `[general]`

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `output_root_target` | string | `$HOME` | Root directory where symlinks are created |
| `no-new-files` | list | `[]` | Paths where new files shouldn't be added/deleted |
| `no-sym` | list | `[]` | File patterns to exclude from symlinking |
| `no-update-on` | list | `[]` | Patterns to skip during push |
| `push-notify-command` | string | - | Command to run on push (use `$!SYM_MESSAGE`) |

#### `[network]`

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `retry-delay-ms` | int | `6000` | Delay between push retries (ms) |
| `max-attempts` | int | `10` | Maximum push attempts |

#### `[path_overrides]`

Key-value pairs mapping relative paths to absolute destinations.

Example:
```toml
[path_overrides]
"keyd" = "/etc/keyd"
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 2 | Git not installed |
| 3 | Not a git repository |
| 4 | No remote origin |

## Contribution Guidelines

This project doesn't accept pull requests. It is primarily for experimenting with AI spec-driven development. Anyone interested can open an issue for bugs or suggestions for improving the spec.

## License

[BSD Zero Clause](LICENSE)
