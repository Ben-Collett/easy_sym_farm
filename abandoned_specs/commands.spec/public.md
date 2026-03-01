in root directory of project, commands.py
all patterns in this are glob style patterns.
class CommandProcessor:
fields:
- config: Config
methods:
- link_all() -> symlinks links all paths using config.paths from there source to destination. 
- unlink_all() -> unlinks all all paths in config.paths
- unlink_source_match_pattern(pattern:str) -> unlink all paths where the source matches the pattern
- push() -> add, commit, push
   1) checks if there are any changes outside of config.no_update return if there isn't
   2) check if there are any files added in any no_new_files directory if there is exits the program and notify the user via stderr and the config.notify_command
   3) if there is a network error will retry based on the config network settings
   4) only executes the git commands if there are any changes which are not in the no update field in the config
   5) if there is a change in any files matched by 
- add(path:Path)
    1) moves file from path to source, resolving any name collision with an _increment
    2) creates a symlink from the new path back to the original
    3) adds to config.paths and writes the config
- add_path_and_group(path:Path,group_path: str)
    1) create a directory inside source at group path ex: group_path="editor/tuis" create source/editor/tuis if it doesn't already exist, will error if the group is outside of source using ..
    2) moves file from path to the new group directory, resolving any name collision with an _increment
    3) creates a symlink from the new path back to the original
    4) adds to config.paths and writes the config
- add_to_git_ignore(pattern:str)-> add pattern to .gitignore in source directory, creates the file and source directory if needed
- remove_from_git_ignore(pattern:str)->remove pattern from .gitignore in source directory, errors if the .gitignore file doesn't exist
- add_to_no_update(pattern) -> add pattern to no_update in config, and write
- remove_from_no_update(pattern) -> remove pattern to no_update in config, and write
- add_to_no_new_files(path:Path) -> add to no new file in config and write, takes a path inside of the source directory, 
- remove_from_no_new_files -> remove from no new file in config and write
- set_config_value(tag, setting, *values)-> sets a value in the config and write
