import os
import re
from typing import Any, Optional

from link_utils import expand_path


class Metadata:
    def __init__(self, source_dir: str, meta_name: str):
        self.source_dir = source_dir
        self.meta_name = meta_name
        self.meta_path = os.path.join(source_dir, meta_name)
        self.data: dict[str, dict[str, Any]] = {
            "general": {},
            "network": {},
            "paths": {},
        }
        self._load()

    def _parse_value(self, value: str) -> Any:
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                return []
            items = []
            current = ""
            in_string = False
            string_char = ""
            for char in inner:
                if char in "\"'":
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                    current += char
                elif char == "," and not in_string:
                    items.append(self._parse_value(current.strip()))
                    current = ""
                else:
                    current += char
            if current.strip():
                items.append(self._parse_value(current.strip()))
            return items
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def _load(self) -> None:
        if not os.path.exists(self.meta_path):
            return
        with open(self.meta_path, "r") as f:
            content = f.read()
        current_section = None
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            section_match = re.match(r"^\[(\w+)\]$", line)
            if section_match:
                current_section = section_match.group(1)
                if current_section not in self.data:
                    self.data[current_section] = {}
                continue
            if current_section and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().strip('"')
                parsed_value = self._parse_value(value.strip())
                self.data[current_section][key] = parsed_value

    def _format_value(self, value: Any) -> str:
        if isinstance(value, str):
            return f'"{value}"'
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            items = [self._format_value(item) for item in value]
            return "[" + ", ".join(items) + "]"
        return str(value)

    def save(self) -> None:
        lines = []
        for section, values in self.data.items():
            if values:
                lines.append(f"[{section}]")
                for key, value in values.items():
                    formatted = self._format_value(value)
                    lines.append(f"{key} = {formatted}")
                lines.append("")
        with open(self.meta_path, "w") as f:
            f.write("\n".join(lines))

    def get_paths(self) -> dict[str, str]:
        paths = self.data.get("paths", {})
        return {k: expand_path(v) for k, v in paths.items()}

    def get_no_new_files(self) -> list[str]:
        return self.data.get("general", {}).get("no-new-files", [])

    def get_no_update_on(self) -> list[str]:
        return self.data.get("general", {}).get("no-update-on", [])

    def get_push_notify_command(self) -> Optional[str]:
        return self.data.get("general", {}).get("push-notify-command")

    def get_retry_delay_ms(self) -> int:
        return self.data.get("network", {}).get("retry-delay-ms", 6000)

    def get_max_attempts(self) -> int:
        return self.data.get("network", {}).get("max-attempts", 10)

    def set_path(self, relative: str, target: str) -> None:
        self.data.setdefault("paths", {})[relative] = target
        self.save()

    def remove_path(self, relative: str) -> None:
        if "paths" in self.data and relative in self.data["paths"]:
            del self.data["paths"][relative]
            self.save()

    def add_to_list(self, section: str, key: str, value: str) -> None:
        self.data.setdefault(section, {})
        if key not in self.data[section]:
            self.data[section][key] = []
        if value not in self.data[section][key]:
            self.data[section][key].append(value)
        self.save()

    def remove_from_list(self, section: str, key: str, value: str) -> None:
        if section in self.data and key in self.data[section]:
            if value in self.data[section][key]:
                self.data[section][key].remove(value)
                self.save()

    def set_value(self, section: str, key: str, value: Any) -> None:
        self.data.setdefault(section, {})[key] = value
        self.save()
