create a cli.py file with which parses the following options, 
`easy_env_sym -h` prints all available flags and the program description
`easy_env_sym help` prints all available flags and the program description

`easy_env_sym link` symlink the files in the source directory

`easy_env_sym unlink` unlinks all symlinked files from the source directory
`easy_env_sym unlink \<pattern\>` unlinks all files relative to the source directory root using the file pattern.

`easy_env_sym push` uses git add, commit, push to push the changes

`easy_env_sym add "\<relative or absolute path\>"` this should take a non symlink file or directory, move it to the source directory, add the path from the source directory 
to original file directory to the paths tag. And link the file. if the file the user is trying to add is already a symlink then error. If there is a file or directory with the same name as the file being linked in the source
then simply put an _increment at the end(ex: file_1 file_2 file_3)

`easy_env_sym add "\<relative or absolute path\> <group_dir>"` all the behaviours of the previous add command should be true except this takes a group dir
which is the name of a directory or directories that should be created in the source directory and the file added to it.
for example if the user runs `easy_env_sym add nvim/ text_editors/tuis` then the `text_editors/tuis` directory and any needed parents should be creaated and the nvim directory copied and symlinked from there.

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
