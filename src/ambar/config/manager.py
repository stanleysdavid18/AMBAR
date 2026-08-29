import json

from ambar.core.paths import application_root


class ConfigManager:
    """
    Lee la configuración del proyecto.
    """

    def __init__(self):

        config_file = application_root() / "config" / "settings.json"

        with open(config_file, "r", encoding="utf-8") as file:
            self.data = json.load(file)

    def update_section(self, section, values):
        self.data[section].update(values)
        config_file = application_root() / "config" / "settings.json"
        config_file.write_text(json.dumps(self.data, ensure_ascii=False, indent=4), encoding="utf-8")

    def get(self, *keys):

        value = self.data

        for key in keys:
            value = value[key]

        return value
