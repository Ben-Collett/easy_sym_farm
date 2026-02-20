import os
from typing import List, Dict, Any, Optional

from link_utils import get_home_dir, get_source_dir, get_meta_name


class Config:
    def __init__(self, source_dir: Optional[str] = None):
        self.source_dir = source_dir or get_source_dir()
        self.meta_name = get_meta_name()
        self.meta_path = os.path.join(self.source_dir, self.meta_name)
        self._ensure_source_dir()
        self._load_config()

    def _ensure_source_dir(self):
        os.makedirs(self.source_dir, exist_ok=True)

    def _parse_toml_simple(self, content: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {"general": {}, "network": {}, "path_overrides": {}}
        current_section = "general"
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                current_section = section_name
                if current_section not in result:
                    result[current_section] = {}
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().strip('"')
                value = value.strip()
                if value.startswith("[") and value.endswith("]"):
                    items = []
                    inner = value[1:-1].strip()
                    if inner:
                        for item in inner.split(","):
                            item = item.strip().strip('"')
                            if item:
                                items.append(item)
                    result[current_section][key] = items
                elif value.startswith('"') and value.endswith('"'):
                    result[current_section][key] = value[1:-1]
                else:
                    try:
                        result[current_section][key] = int(value)
                    except ValueError:
                        result[current_section][key] = value
        return result

    def _serialize_toml_simple(self, data: Dict[str, Any]) -> str:
        lines = []
        for section, values in data.items():
            if values:
                lines.append(f"[{section}]")
                for key, value in values.items():
                    if isinstance(value, list):
                        items = ", ".join(f'"{v}"' for v in value)
                        lines.append(f'"{key}" = [{items}]')
                    elif isinstance(value, str):
                        lines.append(f'"{key}" = "{value}"')
                    else:
                        lines.append(f'"{key}" = {value}')
                lines.append("")
        return "\n".join(lines)

    def _load_config(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                content = f.read()
            self.data = self._parse_toml_simple(content)
        else:
            self.data = {"general": {}, "network": {}, "path_overrides": {}}
        self._set_defaults()

    def _set_defaults(self):
        if "output_root_target" not in self.data["general"]:
            self.data["general"]["output_root_target"] = get_home_dir()
        if "no-new-files" not in self.data["general"]:
            self.data["general"]["no-new-files"] = []
        if "no-sym" not in self.data["general"]:
            self.data["general"]["no-sym"] = []
        if "no-update-on" not in self.data["general"]:
            self.data["general"]["no-update-on"] = []
        if "retry-delay-ms" not in self.data["network"]:
            self.data["network"]["retry-delay-ms"] = 6000
        if "max-attempts" not in self.data["network"]:
            self.data["network"]["max-attempts"] = 10

    def save(self):
        content = self._serialize_toml_simple(self.data)
        with open(self.meta_path, "w") as f:
            f.write(content)

    @property
    def output_root_target(self) -> str:
        return self.data["general"]["output_root_target"]

    @property
    def no_new_files(self) -> List[str]:
        return self.data["general"]["no-new-files"]

    @property
    def no_sym(self) -> List[str]:
        return self.data["general"]["no-sym"]

    @property
    def no_update_on(self) -> List[str]:
        return self.data["general"]["no-update-on"]

    @property
    def push_notify_command(self) -> Optional[str]:
        return self.data["general"].get("push-notify-command")

    @property
    def retry_delay_ms(self) -> int:
        return self.data["network"]["retry-delay-ms"]

    @property
    def max_attempts(self) -> int:
        return self.data["network"]["max-attempts"]

    @property
    def path_overrides(self) -> Dict[str, str]:
        return self.data.get("path_overrides", {})

    def add_to_list(self, section: str, key: str, value: str):
        if section not in self.data:
            self.data[section] = {}
        if key not in self.data[section]:
            self.data[section][key] = []
        if value not in self.data[section][key]:
            self.data[section][key].append(value)

    def remove_from_list(self, section: str, key: str, value: str):
        if section in self.data and key in self.data[section]:
            if value in self.data[section][key]:
                self.data[section][key].remove(value)

    def set_value(self, section: str, key: str, value: Any):
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value

    def add_path_override(self, rel_path: str, abs_path: str):
        if "path_overrides" not in self.data:
            self.data["path_overrides"] = {}
        self.data["path_overrides"][rel_path] = abs_path

    def get_destination_path(self, rel_path: str) -> str:
        if rel_path in self.path_overrides:
            return self.path_overrides[rel_path]
        return os.path.join(self.output_root_target, rel_path)
