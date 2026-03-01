git_wrapper.py is in the project root directory: 
Enum StatusChangeType:
    ADDED
    REMOVED
    MODIFIED

class FileChangeStatus:
    relative_path: str -> relative to the root of the repo
    change_type: StatusChangeType
    
    

Enum GitPushStatus:
    Success
    NetworkError

class: GitWrapper
fields:
- path:pathlib.Path -> the git directory path
methods:
changes(ignored_glob_patterns:Optional\[list\[str\]\])->list\[FileChangeStatus\], returns the relative paths from the source of any files that changed using git status --porclean, which do not match the ignored glob style patterns.
add_all() -> runs git add .
timestamped_commit() -> runs git commit with a time stamp of the following format "YYYY:MM:DD HH:MM:SS" in 24 hour time
push() -> GitPushStatus
runs git push in the path, returns if successful or there was a networkerror

all methods in GitWrapper can throw the following Exceptions:
defined in errors.spec
DirectoryNotFound
FileNotDirectory
MissingRemoteOrigin 
NotAGitRepo


