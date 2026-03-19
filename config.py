import os
import pathlib
from utils import get_home_dir
from typing import Optional
import tomllib


class Config:
    no_new_files: list[str]
    no_update_on: list[str]
    push_notify_command: Optional[str]
    retry_delays_ms: int
    max_attempts: int
    group_order_override: list[str]
    _paths: dict[str, str]

    @staticmethod
    def _config_path() -> pathlib.Path:
        source_dir = os.environ.get("easy_sym_source")
        if source_dir is None:
            home = get_home_dir()
            source_dir = str(home / "easy_syms")

        meta_name = os.environ.get("easy_sym_meta_name", "easy_env_sym_data.toml")
        return pathlib.Path(source_dir) / meta_name

    @staticmethod
    def get_source_directory() -> pathlib.Path:
        source_dir = os.environ.get("easy_sym_source")
        if source_dir is None:
            home = get_home_dir()
            return home / "easy_syms"
        return pathlib.Path(source_dir)

    @staticmethod
    def load() -> "Config":
        config_path = Config._config_path()
        config = Config()

        config.no_new_files = []
        config.no_update_on = []
        config.push_notify_command = None
        config.notify_on_error_only = True
        config.retry_delays_ms = 6000
        config.max_attempts = 10
        config.group_order_override = []
        config._paths = {}

        if not config_path.exists():
            return config

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        if "general" in data:
            general = data["general"]
            if "no-new-files" in general:
                config.no_new_files = general["no-new-files"]
            if "no-update-on" in general:
                config.no_update_on = general["no-update-on"]
            if "push-notify-command" in general:
                val = general["push-notify-command"]
                config.push_notify_command = val if val else None
            if "group-order-override" in general:
                config.group_order_override = general["group-order-override"]

        if "network" in data:
            network = data["network"]
            if "retry-delays-ms" in network:
                config.retry_delays_ms = network["retry-delays-ms"]
            if "max-attempts" in network:
                config.max_attempts = network["max-attempts"]

        if "paths" in data:
            config._paths = dict(data["paths"])

        return config

    def update(self, tag: str, key: str, *values) -> None:
        if tag == "general":
            if key == "no-new-files":
                self.no_new_files = list(values)
            elif key == "no-update-on":
                self.no_update_on = list(values)
            elif key == "push-notify-command":
                self.push_notify_command = values[0] if values else None
        elif tag == "network":
            if key == "retry-delays-ms":
                self.retry_delays_ms = int(values[0])
            elif key == "max-attempts":
                self.max_attempts = int(values[0])

    def add_to_paths(self, source_path: str, target: str) -> None:
        from utils import absolute_path, unexpand_path

        abs_target = absolute_path(target)
        unexpanded_target = unexpand_path(abs_target)
        self._paths[source_path] = str(unexpanded_target)

    def remove_from_paths(self, path: str) -> None:
        from utils import absolute_path

        abs_path = absolute_path(path)
        from utils import unexpand_path

        unexpanded = unexpand_path(abs_path)
        path_str = str(unexpanded)

        keys_to_remove = []
        for key, value in self._paths.items():
            if value == path_str:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._paths[key]

    @property
    def paths(self) -> dict[str, str]:
        return self._paths

    def get_absolute_paths(self) -> dict[str, str]:
        from utils import absolute_path

        result = {}
        for source, target in self._paths.items():
            abs_target = absolute_path(target)
            result[source] = str(abs_target)
        return dict(result)

    def write(self) -> None:
        config_path = self._config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            f.write("[general]\n")
            f.write(f"no-new-files = {self._serialize_list(self.no_new_files)}\n")
            f.write(f"no-update-on = {self._serialize_list(self.no_update_on)}\n")
            cmd = self.push_notify_command
            if cmd:
                f.write(f'push-notify-command = "{cmd}"\n')
            if self.group_order_override:
                f.write(
                    f"group-order-override = {self._serialize_list(self.group_order_override)}\n"
                )

            f.write("\n[network]\n")
            f.write(f"retry-delays-ms = {self.retry_delays_ms}\n")
            f.write(f"max-attempts = {self.max_attempts}\n")

            f.write("\n[paths]\n")
            ordered_groups = self._get_ordered_groups()
            for i, group_name in enumerate(ordered_groups):
                if i > 0:
                    f.write("\n")
                f.write(f"# {group_name}\n")
                sorted_paths = sorted(
                    self._get_grouped_paths()[group_name].items(),
                    key=lambda x: self._path_sort_key(x[0]),
                )
                for source, target in sorted_paths:
                    f.write(f'"{source}" = "{target}"\n')

    def _get_grouped_paths(self) -> dict[str, dict[str, str]]:
        groups: dict[str, dict[str, str]] = {}
        for source, target in self._paths.items():
            group_name = self._get_top_level_group(source)
            if group_name not in groups:
                groups[group_name] = {}
            groups[group_name][source] = target
        return groups

    def _get_top_level_group(self, path: str) -> str:
        if "/" in path:
            return path.split("/")[0]
        return "misc."

    def _get_ordered_groups(self) -> list[str]:
        groups = self._get_grouped_paths()
        override = self.group_order_override

        ordered = []
        remaining = []
        has_misc = False
        misc_in_override = "misc." in override

        for group_name in override:
            if group_name in groups:
                ordered.append(group_name)

        for group in groups:
            if group == "misc.":
                has_misc = True
            elif group not in override:
                remaining.append(group)

        remaining.sort(key=lambda g: g.lower())
        result = ordered + remaining
        if has_misc and not misc_in_override:
            result.append("misc.")
        return result

    def _path_sort_key(self, path: str) -> tuple:
        return tuple(path.split("/"))

    def _serialize_list(self, lst: list[str]) -> str:
        if not lst:
            return "[]"
        return "[" + ", ".join(f'"{item}"' for item in lst) + "]"
