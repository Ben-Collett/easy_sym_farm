create a config.py file in the root directory of the project
this program may depend on utils
the config utils should have the following functionality

a private _config_path this should resolve using two enviomrent variables this should return a PathLib path
1) `$easy_sym_source` this is a path to the directory where all the files that need to be symlinked lives, defaults to $home/easy_syms if not set
2) `$easy_sym_meta_name` the name of the meta data file which is in the source directory, defaults to easy_env_sym_data.toml if not set

a static load function  in the Config class which loads returns a Config(Self) object based on the _config_path()
it should use tomlib to parse the file and set the properties in a Config object

Config should have the following fields 
`no_new_files: list[str]` defaults to empty list, a list of directory paths relative to the source directory root, If a file is added to this directory it should throw an error when trying to push and send a notification
`no_update_on: list[str]` defaults to empty list, a list to determine if any important files updated
`push_notify_command: Optional[str]` defaults to None, a command to send a notification when the push command fails, ex: `notify-send -t 100000 $!SYM_MESSAGE"
`retry_delays_ms:int` defaults to 6000
`max_attempts:int` defaults to 10
config should have a write method to write the updated fields to the config, if the config file or it's parent directories do not exist they should be created.
To farther elaborate it should effectively searlize its self/encode it's self into a map and then use tomllib to write that data in the config.

Config should have a private filed:
- `paths: dict[str:str]`

when loading the config one or every of the fields or even the whole file may not exist if that is the case only override the values that do exist in the default Config. 
Do not error if the file does not exist
the toml file can have following tags and keys
note: that tomllib write doesn't work well with the paths since it doesn't wrap the keys in quotes so a custom write method needs to be written
Make sure your write the paths that are acting as keys in quotes as well as the values
example:
```toml
[general]
no-new-files = []
no-update-on = []
push-notify-command = "" 
[network]
retry-delays-ms = 6000
max-attempts = 10
[paths]
"zellij" = "~/.config/zellij"
# if a group called editors is created
"editors/emacs" = "~/.config/emacs"
"editors/helix" = "~/.config/helix"
```



