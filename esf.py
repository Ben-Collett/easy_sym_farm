import sys
from cli import Parser

if __name__ == "__main__":
    parser = Parser()
    parser.dispatch(*sys.argv[1:])
