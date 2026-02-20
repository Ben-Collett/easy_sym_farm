## Intro
easy_sym_farm is a symlink farm in python similar to stow. That is it should allow the user to take the files from a directory and link them to the target directory and provide an easy way to back up those files to external platforms like github.

## Definitions
Source Directory:
    The directory containing managed files. Defaults to $HOME/easy_syms.

Output Root Target:
    The root directory where symlinks are created. Defaults to $HOME.

Managed File:
    Any file or directory located under the Source Directory and not excluded by no-sym or default exclusions.

Pattern:
    A glob-style pattern interpreted using Python's fnmatch module.
    Patterns are always relative to the Source Directory root unless otherwise specified.

Linked Path:
    The absolute path where a symlink is created.

## Non-functional requirements
1) The project does not rely on any external dependencies.

## Clarifying Rules
Pattern Rules:
- Patterns use Unix-style glob matching via fnmatch.
- Matching is case-sensitive.
- All patterns are evaluated relative to the Source Directory root.
- A pattern matching a directory applies recursively to its contents.


Linking Rules:
1. Links should be created at the highest directory possible, i.e. if a directory can be linked it should be linked instead of linking it's individual files.
2. make sure to avoid bugs like this when you simlink a directory Error: ~/.config/easy_env/abbrs_and_aliases.conf exists and is a regular file, if you symlink the easy_env directory its contents will appear there, there is no reason to symlink the sub files
3. Existing non-symlink files at the destination cause an error.
4. Existing non-symlink directories however do not error and instead there files/subdirectories are symlinked to the new directory, applying all the same linking rules.
5. Existing symlinks pointing to the correct target are left unchanged.
6. Existing symlinks pointing elsewhere cause an error.
7. Hidden files are treated the same as every other file.
8. Symlinks should always be created using absolute paths not relative ones. From one absolute path to another.
9. The permissions of the file including the execution bit should be preserved when linking
10. The linking operation is done very often so any possible optimization should be used


Git Rules:
- The repository root refrened throughout the file is the root of the source directoriy
- The program must use `git status --porcelain`.
- Only unstaged changes are considered.
- Lines starting with '??' indicate new files.
- Deleted files are indicated with ' D' or 'D '.
- Empty commits should not occur, the should be guarded against.
- The commit messages should be a time stamp, at the time of the commit, in 24 hour time using this format: yyyy-mm-dd HH:MM:SS 

Directory Linking Rule:
Directories must be linked as directories (not flattened).
The directory itself is symlinked, not its individual contents,
unless a child is excluded via no-sym.

Error Reporting Rule:
All errors must:
- Print a clear human-readable message to stderr.
- Exit with the defined exit code.
- Not print stack traces.
- if it is a push error, notify the user using the notify command.

Unlink Rule:
The unlink command must:
- Remove only symlinks that point to files under the Source Directory.
- Leave non-symlink files untouched.
- Remove empty parent directories created during linking.
- 
Creation Rule:
 If a directory/file is needed to exist then it should be created.
 for example the metadata, the source directory, the target directory, in all cases if they do not exist and a call modifies them they should be created.
Home Resolution Rule:
The home directory must be resolved using the SUDO_USER environment variable if present.
Otherwise, use the current user’s home directory.
Do not use os.path.expanduser("~") directly when running under sudo.

Deterministic Traversal Rule:
Files must be traversed in lexicographic sorted order
based on their relative path from the Source Directory.
Traverse directories first and remember that if a directory gets symlinked from the source dir
or was already symlniked from the source dir there is no reason to traverse it's children.

Network Failure Definition:
A push failure is considered network-related if git returns a non-zero exit code and stderr contains:
- "Could not resolve host"
- "Connection timed out"
- "Failed to connect"

Path Override Resolution Rules:
- If a relative path P exists under [path_overrides],
the symlink target is the override path instead of
Output Root Target / P.
- path resolution is lower precdence then no-sym and no-new-files that is to say even if a path is overridden it must respect those two lists

Override Safety Rule:
Path overrides must be absolute paths.
Relative overrides are invalid.

Ancestor Precedence Rule:
If linking directory A would encompass an already-linked child B,
the program must:
1. Unlink B.
2. Link A.
3. Ensure no duplicate symlinks exist.

Atomicity Requirement:
If any link operation fails, the program must:
- Stop immediately
- Leave already-created links intact
- Print a summary of successful and failed operations

Link Algorithm:

For each file F in Source Directory:
1. Skip if F matches no-sym.
2. Skip if F is in default exclusions.
3. Determine destination path D using the path override if there is one
4. If D is a directory that is already symlinked from the source then stop traversing down that branch of the file tree
5. If D is a directory that already exist then don't link it, recurse and link its descendents instead
6. Ensure parent directory of D exists create it if it doesn't.
7. If D exists:
   a. If D is a symlink pointing to F → skip.
   b. If D is a symlink pointing elsewhere → error.
   c. If D is a regular file → error.
8. Create symlink from D → F.
## Environment variables 
There are two environment variables that effect the functionality of easy_sym_farm

1) `$easy_sym_source` this is a path to the directory where all the files that need to be symlinked lives, defaults to $home/easy_syms if not set. At any farther point in the specification this directory may be referred to as the source directory
2) `$easy_sym_meta_name` the name of the meta data file which is in the source directory, defaults to easy_env_sym_data.toml

## Metadata File
The meta data file is a toml used to store important information for linking.

the following fields should be under the `[general]` tag
`output_root_target` this is the root directory where the files are symlinked to this should default to the home directory if it is not set.

`no-new-files` is a list of paths to file directories where new files shouldn't be created, deleted nor renamed. They can however be modified.
What this practically means that if a user tries to do a normal push the program will check if any of these directories had a new file added or deleted,
using git status. If any files where added or removed then the program will error and exit, WITHOUT RUNNING git add. The check must occur before the git add logic.
This can be used so that a user avoids accedntially committing secrets for example if a user adds there shell to the no-new-files list, `"no-new-files" = ["fish"]`
and they later added a `secrets.fish` file to there fish directory it would avoid the user accedntially, absentmindidly, committing those secrets. If a directory is passed in the rule applies to all of its subdirectries as well

`no-sym` a list of file patterns that should not be symlinked, relative to the root path for example you might have `no-sym = [fish/nonsense.fish]` to exclude the nonsense.fish file from being symlinked. Defaults to an empty list

`no-update-on` these are a list of file patterns for helping determine when a git add, commit, and push should occur.
Essentially if after running git status all the changed files match patterns in the no-update-on list then the files should not be git added/commited/pushed.
this is so a user can have a file in there repo that doesn't necessarily need to be backed up every time for example 
one might do `on-update-on = ["nvim/lazyvim.json", "nvim/lazy-lock.json"]` to avoid updating there repo when using lazy to update there programs


`push-notify-command` when the program fails or succeeds at pushing and the program exits and prints an error or that it successfully pushed. If a notify-command is set it will also run that command before erroring. An example might be `notify -t 100000 $!SYM_MESSAGE` the $!SYM_MESSAGE in the command should be substatuted by the actual meassage the user needs to receive. The notify command is not set to anything by default.

the following fields should be under the `[network]` tag
if a push can't occur because the device is not connected to the internet/can't reach the domain then the program should return the connection
every `retry-delay-ms` for `max-attempts` the push-notify-command should only notify for the last failure/success not any intermidary failures do to the network
`retry-delay-ms` default to 6000
`max-attempts` defaults to 10 
`[path_overrides] tag` a tag where each key value pair under the tag is a mapping that overrides the path where the file/directory is symlinked
for example you might have this `"keyd" = "/etc/keyd"`
## CLI interface
`easy_env_sym -h` or `easy_env_sym help` prints all available flags and the program description

`easy_env_sym link` symlink the files in the source directory

`easy_env_sym unlink` unlinks all symlinked files from the source directory
`easy_env_sym unlink \<pattern\>` unlinks all files relative to the source directory root using the file pattern.

`easy_env_sym push` uses git add, commit, push to push the changes
`easy_env_sym add "\<relative or absolute path\>"` this should take a file or directory which is in the output_root_target or one of its subdirectories. If it is not then the program should error.
if it is then the file/directory should be moved to the correspoiding relative path from the output_target_root in the source directory.
for example if the output_target_root was the home directory ~ and the user was in `~/.config/`
and ran `easy_env_sym add nvim` then the nvim directory should be moved to $eas_env_sym_source(or the home directory)/.config/nvim
and then that directory should be symlinked to the absolute path of the original /home/<username>/.config/nvim

`easy_env_sym add "\<relative or absolute path\> \<relative or absolute path\>"` this works similarly to the regulare add except it does not verify it is under the output_target_dir.

Instead it takes two paths
the first path is the relative path it will appear under in the source dir.
the second is the path to the file that's is to be symlinked which will be converted to an absolute path by the program if it is a relative path
this is achieved by adding it to the path_overrides tag

`easy_env_sym add-to-git-ignore \<pattern\>` adds a pattern to the .gitignore file
`easy_env_sym remove-from-git-ignore \<pattern\>` removes a pattern from the .gitignore file

`easy_env_sym add-to-no-update \<pattern\>` adds a file pattern to the no-update-on list in the toml file
`easy_env_sym remove-from-no-update \<pattern\>` removes a file pattern from the no_update_on list in the toml file

`easy_env_sym add-to-no-new-files \<relative path\>` adds a path relative to the source directory to the no-new-files list in the toml file
`easy_env_sym remove-from-no-new-files \<relative path\>` removes a path from the no-new-files list in the toml file

`easy_env_sym add-to-no-sym \<pattern\>` adds a file pattern to the no-sym list in the toml file
`easy_env_sym remove-from-no-sym \<pattern\>` removes a file pattern from the no-sym list in the toml file

`easy_env_sym set source \<path\>` sets the source directory path environment variable, this should also run unlink before it changes the value then link after it changes the value
inorder to move all the symlinks.
`easy_env_sym set meta-name \<name\>` sets the meta data file name environment variable
`easy_env_sym set \<tag\> \<setting\> \<value(s)\>` this should allow the user to set any value from the config


## Exit Codes
0 = success
1 = general failure
2 = git not installed
3 = not a git repository
4 = no remote origin


## Installation
include a `dumb_build.toml` file in the repo
with this content:
```toml
[build]
executable_name = "esf"
command = "python $dumb_project_dir/easy_sym_farm.py"
excluded = [
  ".gitignore",
  "__pycache__",
  "images",
  "keyboard/__pycache__",
  ".ruff_cache",
  "dumb_build.toml",
  "test.py",
  "LICENSE",
  "README.md",
]
local_install_excluded = [".git"]
```
The user can run `din Ben-Collett/easy_sym_farm` to install the program without them needing to directly clone the repo themselves.
(din is the command to run dumb installer which automatically clones the repo to a certain location automatically)

The user can install dumb_installer from the repo: https://github.com/Ben-Collett/dumb_installer

The user can ofcourse also just clone the repo and run the easy_sym_farm.py file without doing a full install.

## Contribution Guildlines
This project doesn't accept pull request, it is primarily for me to experiment with the idea of AI spec driven development.
Any one interested can make an issue if they find any and make any suggestions for improvoment to the spec.

## License
BSD Zero Clause License

Copyright (c) 2026 Benjamin Collett 

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

## Code Structure
### File Structure
easy_sym_farm.py
errors.py
cli.py
.gitignore -> should ignore all cache files, and only cache files. example: __pycache__, .ruff_cache
git_wrapper.py -> contains a wrapper class for all the git functionality
link_utils.py -> utils for handling symlinking
LICENSE -> BSD Zero
README.MD
Any additional needed files can be created.

### Code Organization rules
- No file may exceed 400 lines.
- No function may exceed 50 lines.
- Functions must do one logical operation.
- No function may handle both IO and business logic.

### Readme
The read me should include:
- A disclaimer that the code was written using AI spec driven development at the top of the readme
- A brief overview of what the program is
- instructions on how to install the program using dumb_installer including a link to the repo to install dumb_installer if the user doesn't have it already.
- An explanation of how to clone the repo and run the program without installing it `git clone https://github.com/Ben-Collett/easy_sym_farm`,`python easy_sym_farm.py`
- A description of each flag and configuration option available
- The contribution guidelines
- The name of the license that links to the LICENSE file

## Edge cases
1) If a runs easy_env_sym push and git is not installed exit with an error and print git not installed 
2) If easy_env_sym push is run and git is installed but the directory is not an initialized git directory exit and print the matching exit code definition
3) If easy_env_sym push is run and the directory is initialized but there is no remote origin exits and prints no remote origin found.
4) There are a few files which should not be symlinked by default namely the .git directory, the .gitignore file, and the metadata file.
5) If because of a path override a symlink requires root privlages to create then a user should be notified so they can run the command with root privlages. Write privlages to the link should be made as root only for security reasons.
6) Even if the user runs the command with sudo it must use the users home directory not the root users home directory
7) If the user tries to symlink a directory or a file that is a sub directory of an already symlinked directory(from the source directory) stop them and error.
8) If a user symlinks a directory which has a sub directory or file already linked from the source directory then unlink the sub directory/file and link the ancestor directory.

## Acceptance Criteria
The implementation is complete when:
- All CLI commands operate as defined.
- Linking is deterministic.
- Git push obeys all no-new-files and no-update-on rules.
- Retry logic obeys max-attempts and retry-delay-ms.
- No external dependencies are used.
- Default exclusions (.git, metadata file, .gitignore) are enforced.
- Unlink followed by link results in identical filesystem state.
- All code structure and orginzation rules are followed.
- The readme has all the required components.
