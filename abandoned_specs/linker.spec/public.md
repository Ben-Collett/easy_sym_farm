linker.py file in the root directory of the project
link(source, dest) should take two path lib paths and create a symlink from p1 to p2, throws Exceptions if the source doesn't exist or the destination exist and is not symlinked from the source. Should convert paths to absolute paths. 
unlink(source:Path,config:Config)-> takes a source directory Path and a config
