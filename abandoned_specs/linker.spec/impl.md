link(source, dest) should take two path lib paths and create a symlink from p1 to p2
- if dest already exist and is a symlink from source then the function should return
- if dest exist and is not a symlink from source then the function should throw an Exception
- if source doesn't exist an exception should be thrown
- the paths may be directories
- if dest's parents don't exist they should be created
unlink(source:Path,config:Config)-> takes a source directory Path and a config
- if source is not in config.paths.keys() throw an exception
- map source to its destination using paths
- test if the destination is a symlink and is linked from the source if not throw an exception
- delete the destination if it is a symlink linked from source
