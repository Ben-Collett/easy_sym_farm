each error/exception extends Exception or a subclass of exception(based on the Base exception in each section), and should have a field called message which is the default message for the error
unless specified they do not take any arguments/have any fields
# Git Exceptions
Base: GitError -> there was a git error at path
fields: path: Pathlib.Path
MissingRemoteOrigin -> couldn't find remote origin for path
fields:path
NotAGitRepo-> path is not a git repository
fields: path

# Linking Exceptions
Base: LinkingError() -> there was an error linking
FileAlreadyExist-> couldn't link file existing dest_path
fields: dest_path
LinkPermissionDenied-> Permission Error: failed to create/remove(based on creating flag) link at dest_path.
fields:dest_path, creating:bool  

# File
base: CustomFileException -> file exception path
- path
DirectoryNotFound() -> directory not found at path
- path
FileNotDirectory() -> path is a file not a directory
- path 
