"""Almacenamiento local de claves de proveedores, separado de settings.json."""

import os

from PySide6.QtCore import QSettings


class ApiKeyStore:
    """Prioriza la clave guardada para el usuario actual y luego el entorno."""

    KEY_NAMES = ("GROQ_API_KEY", "GEMINI_API_KEY", "CEREBRAS_API_KEY", "OPENAI_API_KEY")

    def __init__(self, settings=None, environ=None):
        self._settings = settings or QSettings("AMBAR", "AMBAR")
        self._environ = os.environ if environ is None else environ

    def get(self, name):
        if name not in self.KEY_NAMES:
            raise ValueError(f"Clave no admitida: {name}")
        saved = str(self._settings.value(f"api_keys/{name}", "") or "").strip()
        return saved or str(self._environ.get(name, "") or "").strip()

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
