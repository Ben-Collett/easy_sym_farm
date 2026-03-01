config.py in the root directory
has a public class Config
Config 
has the following static methods:
- load() loads the config object for the current envronment
- get_source_directory() -> Pathlib.Path
the following public fields
- `no_new_files: list[str]` 
- `no_update_on: list[str]` 
- `push_notify_command: Optional[str]` 
- `retry_delays_ms:int` 
- `max_attempts:int` 
methods: 
- update(tag:str, key:str, *values)-> updates based on a key value pair in the toml, does not write the change only changes the config instance
- add_to_paths(source_path:str,target:str):
    1) converts the target to it's absolute form then unexpands it using utils
    2) adds to the underline paths dict the source path as a key and the target as the value
- remove_from_paths(path:str) -> takes a path converts it to its absolute form, converts the home directory using ~.
- get_absolute_paths()-> returns an immutable dict\[str:str\] of each path in the config._paths converted to there absolute form

