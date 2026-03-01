from pathlib import Path

from config import Config
from utils import expand_path
from typing import Optional
from ansii import RED, BLUE, RESET, BOLD
from dataclasses import dataclass


@dataclass
class LinkData:
    already_linked: bool = False
    msg: Optional[str] = None


def link(source: Path, dest: Path) -> LinkData:
    if not source.exists():
        return LinkData(msg=f"{RED}can't link source does not exist: {BLUE}{BOLD}{source}{RESET}")

    if dest.is_symlink():
        if dest.resolve() == source.resolve():
            return LinkData(already_linked=True)
        return LinkData(msg=f"""
    {RED}Destination exists but is not a symlink to source
    source is {BLUE}{BOLD}{source}{RESET}{RED}
    destination is{BLUE}{BOLD}{dest}
    {RED}destination resolves to {BLUE}{BOLD}{dest.resolve()}
    """)

    if dest.exists():
        return LinkData(msg=f"{RED}{BOLD}LINK FAILED{RESET}, {RED}destination already exist {BLUE}{BOLD}{dest.absolute()}")

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(source)
        return LinkData()
    except PermissionError:
        return LinkData(msg=f"{RED}{BOLD}PERMISSION DENIED{RESET}{RED}, can't link to {BOLD}{BLUE}{dest.absolute()}{RED} {RESET}")


# returns an error message or None if successful
def unlink(source: Path, config: Config) -> Optional[str]:
    source_str = str(source.relative_to(Config.get_source_directory()))
    if source_str not in config.paths.keys():
        raise ValueError(f"Source not in config.paths: {source}")

    dest = expand_path(Path(config.paths[source_str]))

    if not dest.exists():
        return None

    if not dest.is_symlink():
        return f"{RED}can't unlink destination is not a symlink: {BLUE}{BOLD}{dest}{RESET}"

    if dest.resolve() != source.resolve():
        return f"{RED}can't unlink destination is not a symlink: {BLUE}{BOLD}{dest}{RESET}"
    try:
        dest.unlink()
        return None
    except PermissionError:
        return f"{RED}{BOLD}PERMISSION DENIED{RESET}{RED}, can't unlink {BOLD}{BLUE}{dest.absolute()}{RED} {RESET}"
