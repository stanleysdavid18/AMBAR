import json

from ambar.core.paths import application_root, writable_config_root


class ConfigManager:
    """Lee defaults empaquetados y persiste ajustes en una ubicación escribible."""

    def __init__(self):
        bundled = application_root() / "config" / "settings.json"
        persisted = writable_config_root() / "settings.json"
        self._config_file = persisted if persisted.exists() else bundled
        with self._config_file.open("r", encoding="utf-8-sig") as file:
            self.data = json.load(file)

    def update_section(self, section, values):
        self.data[section].update(values)
        config_file = writable_config_root() / "settings.json"
        config_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=4), encoding="utf-8")
        self._config_file = config_file

    def get(self, *keys):
        value = self.data
        for key in keys:
            value = value[key]
        return value
