implement a parser that parses each of these commands from argv, using commands
this should only depend on commands.py and pythons standard library.

create a cli.py file with which defines a parser abject with a dispatch method which matches the following options.
Implement a custom help message to show each option available
display the help message if the user runs the esf without a 
don't include the actual command in the help message do something more like:

\<program descritipon\>
flags: 
    -h -> print all available flags, what they do and a brief program description
Subcommands:
    link-> \<description\>
    add <file> -> \<description\> 
    add <file> <group> -> \<description\>
use ansii to color the flags and the subcommnands
    
`esf -h` prints all available flags and the program description
`esf help` prints all available flags and the program description

`esf link` symlink the files in the source directory

`esf unlink` unlinks all symlinked files from the source directory
`esf unlink \<pattern\>` unlinks all files relative to the source directory root using the file pattern.

`esf push` uses git add, commit, push to push the changes

`esf add "\<relative or absolute path\>"` this should take a non symlink file or directory, move it to the source directory, add the path from the source directory 
to original file directory to the paths tag. And link the file. if the file the user is trying to add is already a symlink then error. If there is a file or directory with the same name as the file being linked in the source
then simply put an _increment at the end(ex: file_1 file_2 file_3)
`esf add "\<relative or absolute path\> <group_dir>"` all the behaviours of the previous add command should be true except this takes a group dir
which is the name of a directory or directories that should be created in the source directory and the file added to it.
for example if the user runs `esf add nvim/ text_editors/tuis` then the `text_editors/tuis` directory and any needed parents should be creaated and the nvim directory copied and symlinked from there.

`esf add-to-git-ignore \<pattern\>` adds a pattern to the .gitignore file

`esf remove-from-git-ignore \<pattern\>` removes a pattern from the .gitignore file

`esf add-to-no-update \<pattern\>` adds a file pattern to the no-update-on list in the toml file
`esf remove-from-no-update \<pattern\>` removes a file pattern from the no_update_on list in the toml file

`esf add-to-no-new-files \<relative path\>` adds a path relative to the source directory to the no-new-files list in the toml file
`esf remove-from-no-new-files \<relative path\>` removes a path from the no-new-files list in the toml file
`esf set \<tag\> \<setting\> \<value(s)\>` this should allow the user to set any value from the config


