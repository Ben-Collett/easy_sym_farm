# easy_sym_farm

**Disclaimer: This project was created using AI spec-driven development.**

A symlink farm manager similar to GNU Stow, written in Python. It allows you to manage configuration files by storing them in a central directory and creating symbolic links to them from their expected locations.

## Overview

easy_sym_farm helps you:
- Keep your dotfiles organized in a single directory (default: `~/easy_syms`)
- Create symbolic links to those files in their target locations
- Push changes to git for backup
- Manage which files should and shouldn't be symlinked
- Override paths for special cases (e.g., system files in `/etc`)

## Requirements

- Python 3.7+ (no external dependencies required)
- Git (for the push functionality)

## Installation

Simply make the script executable and place it in your PATH:

```bash
chmod +x easy_sym_farm.py
# Option 1: Add to a directory in your PATH
sudo cp easy_sym_farm.py /usr/local/bin/easy_sym_farm
# Option 2: Create a symlink
ln -s $(pwd)/easy_sym_farm.py ~/bin/easy_sym_farm
```

## Quick Start

```bash
# Initialize the source directory
easy_sym_farm link

# Add an existing config file to manage
easy_sym_farm add ~/.config/nvim

# Create all symlinks
easy_sym_farm link

# Push changes to git
easy_sym_farm push
```

## Environment Variables

- **`$easy_sym_source`**: Path to the source directory where all managed files are stored. Defaults to `$HOME/easy_syms`.
- **`$easy_sym_meta_name`**: Name of the metadata configuration file. Defaults to `easy_env_sym_data.toml`.

## Configuration

The configuration file is located at `$easy_sym_source/$easy_sym_meta_name` (default: `~/easy_syms/easy_env_sym_data.toml`).

### Configuration Options

#### `[general]` Section

- **`output_root_target`**: The root directory where symlinks are created. Defaults to `$HOME`.
- **`no-new-files`**: List of paths where new files cannot be added, deleted, or renamed (only modified). Useful for preventing accidental commits of secrets.
- **`no-sym`**: List of glob patterns for files/directories that should not be symlinked.
- **`no-update-on`**: List of glob patterns. If all changed files match these patterns, git operations are skipped.
- **`push-notify-command`**: Command to run after push success/failure. Use `$!SYM_MESSAGE` as a placeholder for the message.

#### `[network]` Section

- **`retry-delay-ms`**: Delay between retry attempts (default: 6000ms)
- **`max-attempts`**: Maximum number of push retry attempts (default: 10)

#### `[path_overrides]` Section

Override where specific files/directories are symlinked. For example:

```toml
[path_overrides]
"keyd" = "/etc/keyd"
```

## Commands

### `easy_sym_farm link`

Creates symbolic links from the source directory to the target locations.

**Rules:**
- Files are traversed in lexicographic sorted order (deterministic)
- Existing correct symlinks are left unchanged
- Existing files cause an error (won't overwrite)
- Existing symlinks pointing elsewhere cause an error
- Directories are symlinked as directories (not flattened)
- Parent directories are created as needed

### `easy_sym_farm unlink [pattern]`

Removes symlinks that point to files in the source directory.

- If `pattern` is provided, only unlink files matching the pattern
- Only removes symlinks that point to the source directory
- Leaves non-symlink files untouched
- Removes empty parent directories created during linking

### `easy_sym_farm push`

Commits and pushes changes to the git remote.

**Features:**
- Uses `git status --porcelain` to check for changes
- Respects `no-new-files` restrictions (prevents commits with new/deleted files)
- Respects `no-update-on` patterns (skips push if all changes match)
- Retries on network failures according to network settings
- Creates timestamp-based commit messages (format: `yyyy-mm-dd HH:MM:SS`)
- Runs notify command on success/failure (if configured)

**Exit Codes:**
- 0: Success
- 2: Git not installed
- 3: Not a git repository
- 4: No remote origin

### `easy_sym_farm add <path>`

Moves a file/directory from its current location into the source directory and creates a symlink.

- The path must be under `output_root_target` (typically `$HOME`)
- Example: `easy_sym_farm add ~/.config/nvim` moves `~/.config/nvim` to `~/easy_syms/.config/nvim` and symlinks it back

### `easy_sym_farm add <source-path> <target-path>`

Adds a path override for files outside the standard output root.

- `source-path`: Relative path within the source directory
- `target-path`: Absolute path to the actual file location
- Example: `easy_sym_farm add "keyd" "/etc/keyd"`

### `easy_sym_farm add-to-git-ignore <pattern>`

Adds a pattern to the `.gitignore` file in the source directory.

### `easy_sym_farm remove-from-git-ignore <pattern>`

Removes a pattern from the `.gitignore` file.

### `easy_sym_farm add-to-no-update <pattern>`

Adds a pattern to the `no-update-on` list in the configuration.

### `easy_sym_farm remove-from-no-update <pattern>`

Removes a pattern from the `no-update-on` list.

### `easy_sym_farm add-to-no-new-files <path>`

Adds a path to the `no-new-files` list in the configuration.

### `easy_sym_farm remove-from-no-new-files <path>`

Removes a path from the `no-new-files` list.

### `easy_sym_farm add-to-no-sym <pattern>`

Adds a pattern to the `no-sym` list (files to exclude from symlinking).

### `easy_sym_farm remove-from-no-sym <pattern>`

Removes a pattern from the `no-sym` list.

### `easy_sym_farm set <setting> [value]`

Sets configuration values.

**Special settings:**
- `set source <path>`: Changes the source directory (runs unlink before and link after)
- `set meta-name <name>`: Changes the metadata file name

**Config settings:**
- `set <tag>.<setting> <value>`: Sets a value under a specific tag (e.g., `set network.max-attempts 5`)
- `set <setting> <value>`: Sets a value under `[general]` (e.g., `set output_root_target /home/user`)

### `easy_sym_farm help`

Shows the help message with all available commands.

## Pattern Matching

Patterns use Unix-style glob matching via Python's `fnmatch` module:
- `*` matches any sequence of characters
- `?` matches any single character
- `[seq]` matches any character in seq
- Matching is case-sensitive
- Patterns ending with `/` or `/*` match directories recursively

## Default Exclusions

The following are automatically excluded from symlinking:
- `.git/` directory
- `.gitignore` file
- The metadata file (default: `easy_env_sym_data.toml`)

## Sudo Support

When running with sudo, the program uses the original user's home directory (from `SUDO_USER`) instead of `/root`.

## Examples

### Basic Setup

```bash
# Initialize
easy_sym_farm link

# Add your shell config
easy_sym_farm add ~/.bashrc
easy_sym_farm add ~/.bash_profile

# Add a directory
easy_sym_farm add ~/.config/i3

# Create all links
easy_sym_farm link

# Push to git
easy_sym_farm push
```

### Exclude Files from Symlinking

```bash
# Don't symlink temporary files
easy_sym_farm add-to-no-sym "*.tmp"
easy_sym_farm add-to-no-sym "*.swp"

# Exclude a specific directory
easy_sym_farm add-to-no-sym "nvim/temp"
```

### Manage System Files

```bash
# Add an override for a system file
easy_sym_farm add "keyd" "/etc/keyd"

# This requires sudo for linking
easy_sym_farm link
```

### Prevent Accidental Secret Commits

```bash
# Add a directory to no-new-files
easy_sym_farm add-to-no-new-files "fish"

# Now if you add a new file to the fish directory,
# push will fail before committing
```

### Skip Unnecessary Commits

```bash
# Don't push when only lock files change
easy_sym_farm add-to-no-update "nvim/lazy-lock.json"
easy_sym_farm add-to-no-update "*/lazy-lock.json"
```

### Setup Notifications

```toml
# In easy_env_sym_data.toml
[general]
push-notify-command = "notify-send -t 5000 $!SYM_MESSAGE"
```

## Troubleshooting

### Permission Denied

If linking fails with permission errors for system directories, run with sudo:
```bash
sudo easy_sym_farm link
```

### Git Not Initialized

Before using `push`, initialize git in the source directory:
```bash
cd ~/easy_syms
git init
git remote add origin <your-repo-url>
```

### Symlink Conflicts

If a file already exists at the destination:
1. Remove or rename the existing file
2. Run `easy_sym_farm link` again

## License

This project is in the public domain. Use it as you wish.

## Contributing

Contributions are welcome! Please ensure your changes maintain compatibility with the existing behavior and don't add external dependencies.
