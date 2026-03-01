import os
import pathlib
from typing import Optional


class Config:
    no_new_files: list[str]
    no_update_on: list[str]
    push_notify_command: Optional[str]
    retry_delays_ms: int
    max_attempts: int
    _paths: dict[str, str]

    @staticmethod
    def _config_path() -> pathlib.Path:
        source_dir = os.environ.get("easy_sym_source")
        if source_dir is None:
            home = Config._get_home_dir()
            source_dir = str(home / "easy_syms")

        meta_name = os.environ.get(
            "easy_sym_meta_name", "easy_env_sym_data.toml")
        return pathlib.Path(source_dir) / meta_name

    @staticmethod
    def _get_home_dir() -> pathlib.Path:
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            return pathlib.Path(f"/home/{sudo_user}")
        return pathlib.Path.home()

    @staticmethod
    def get_source_directory() -> pathlib.Path:
        source_dir = os.environ.get("easy_sym_source")
        if source_dir is None:
            home = Config._get_home_dir()
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
        config._paths = {}

        if not config_path.exists():
            return config

        import tomllib

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
            f.write(
                f"no-new-files = {self._serialize_list(self.no_new_files)}\n")
            f.write(
                f"no-update-on = {self._serialize_list(self.no_update_on)}\n")
            cmd = self.push_notify_command
            if cmd:
                f.write(f'push-notify-command = "{cmd}"\n')

            f.write("\n[network]\n")
            f.write(f"retry-delays-ms = {self.retry_delays_ms}\n")
            f.write(f"max-attempts = {self.max_attempts}\n")

            f.write("\n[paths]\n")
            for source, target in self._paths.items():
                f.write(f'"{source}" = "{target}"\n')

    def _serialize_list(self, lst: list[str]) -> str:
        if not lst:
            return "[]"
        return "[" + ", ".join(f'"{item}"' for item in lst) + "]"
