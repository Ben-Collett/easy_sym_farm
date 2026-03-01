utils.py is in the project root directory: 
1) expand_path(pathlib Path)-> expands the users path, if the program is being ran with sudo then it will resolve to the person who called sudo's path not the root users home path
2) unexpand_path(Path)-> the inverse of expand path subtatues the users home path with a ~, again if running as sudo it will use the caller of sudos path not the sudo users home path. 
3) absolute_path(path:Path|str)-> pathlib.Path -> takes a string and if it is an absolute path returns it, if it starts with a ~ expands it, and if it is not a absolute path it is treated as a relative path from the current working directory.
in absolute path if the path is a Path it is onverted to an str using this
    if isinstance(path, pathlib.Path):
        path = str(path.absolute())

note: non of these functions resolve symlinks


