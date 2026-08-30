"""Wizard mínimo de primer uso: no necesita cloud para ejecutar skills."""

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from ambar.config.manager import ConfigManager


class FirstRunWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bienvenida a Ámbar")
        self.setMinimumWidth(390)
        layout = QVBoxLayout(self)
        title = QLabel("Configura cómo quieres usar Ámbar")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        explanation = QLabel(
            "Sin una key, Ámbar puede abrir aplicaciones y usar sus skills. "
            "Para conversar rápido necesitas Ollama local o una API key propia."
        )
        explanation.setWordWrap(True)
        self.local_button = QPushButton("Modo local (Ollama / sin cloud)")
        self.cloud_button = QPushButton("Modo cloud propio (configurar keys en ⚙️)")
        self.local_button.clicked.connect(lambda: self._choose("local"))
        self.cloud_button.clicked.connect(lambda: self._choose("auto"))
        layout.addWidget(title)
        layout.addWidget(explanation)
        layout.addWidget(self.local_button)
        layout.addWidget(self.cloud_button)

    def _choose(self, mode):
        ConfigManager().update_section("ai", {"mode": mode})
        QSettings("AMBAR", "AMBAR").setValue("onboarding/completed", True)
        self.accept()
