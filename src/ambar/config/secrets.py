"""Claves locales del usuario y, opcionalmente, de una compilación de pruebas."""

import json
import os

from PySide6.QtCore import QSettings

from ambar.core.paths import writable_config_root


class ApiKeyStore:
    """Prioriza claves del usuario; las de desarrollo solo se leen en modo pruebas."""

    KEY_NAMES = ("GROQ_API_KEY", "GEMINI_API_KEY", "CEREBRAS_API_KEY", "OPENAI_API_KEY")

    def __init__(self, settings=None, environ=None, dev_secrets_path=None):
        self._settings = settings or QSettings("AMBAR", "AMBAR")
        self._environ = os.environ if environ is None else environ
        self._dev_secrets_path = dev_secrets_path or (writable_config_root() / "dev_secrets.json")

    @property
    def developer_mode(self):
        try:
            value = self._settings.value("developer/testing_mode", False, type=bool)
        except TypeError:  # adaptadores simples usados en pruebas
            value = self._settings.value("developer/testing_mode", False)
        return str(value).casefold() in {"1", "true", "yes", "on"}

    def get(self, name):
        if name not in self.KEY_NAMES:
            raise ValueError(f"Clave no admitida: {name}")
        saved = str(self._settings.value(f"api_keys/{name}", "") or "").strip()
        if saved:
            return saved
        if self.developer_mode:
            dev_value = str(self._dev_secrets().get(name, "") or "").strip()
            if dev_value:
                return dev_value
        return str(self._environ.get(name, "") or "").strip()

    def dev_secrets_available(self):
        return self.developer_mode and bool(self._dev_secrets())

    def _dev_secrets(self):
        try:
            data = json.loads(self._dev_secrets_path.read_text(encoding="utf-8"))
            return {key: data[key] for key in self.KEY_NAMES if isinstance(data.get(key), str)}
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

    def save(self, values):
        for name, value in values.items():
            if name not in self.KEY_NAMES:
                raise ValueError(f"Clave no admitida: {name}")
            cleaned = str(value or "").strip()
            if cleaned:
                self._settings.setValue(f"api_keys/{name}", cleaned)
        self._settings.sync()

    @staticmethod
    def mask(value):
        value = str(value or "").strip()
        if not value:
            return "Sin guardar"
        if len(value) <= 8:
            return "••••"
        return f"{value[:3]}…{value[-4:]}"

