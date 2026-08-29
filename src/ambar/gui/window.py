from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from ambar.core.state import SystemState
from ambar.gui.avatar import AvatarWidget


class AmberWindow(QWidget):
    _DISPLAY = {
        SystemState.OFFLINE: "Desconectada", SystemState.STARTING: "Iniciando...",
        SystemState.READY: "Lista", SystemState.SLEEPING: "Dormida",
        SystemState.LISTENING: "Escuchando...", SystemState.THINKING: "Pensando...",
        SystemState.SPEAKING: "Hablando...", SystemState.ERROR: "Ocurrió un error",
    }

    def __init__(self, events):
        super().__init__()
        self._events = events
        self._settings = QSettings("AMBAR", "AMBAR")
        self._drag_offset = None
        self._show_microphone_button = self._settings.value("ui/show_microphone_button", True, type=bool)
        self._microphone_enabled = self._transcription_active = self._developer_mode = False

        self.setWindowTitle("Ámbar")
        self.setMinimumSize(280, 320)
        self.resize(340, 390)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("QWidget { background: #140f1f; color: #f7efff; font-family: Segoe UI; } QPushButton { background: #342547; border: 1px solid #795ca0; border-radius: 12px; padding: 7px 10px; } QPushButton:hover { background: #4b3565; } QLabel { color: #eadcf7; }")
        self.restoreGeometry(self._settings.value("window/geometry", b""))

        self.avatar = AvatarWidget()
        self.name = QLabel("ÁMBAR")
        self.status = QLabel("Dormida")
        self.mode_status = QLabel("MODO: NORMAL • CASUAL: DESACTIVADO")
        self.transcript = QLabel("")
        for label in (self.name, self.status, self.mode_status, self.transcript):
            label.setAlignment(Qt.AlignCenter)
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.transcript.setWordWrap(True)

        self.settings_button = QPushButton("⚙️")
        self.quick_microphone_button = QPushButton("🎤")
        self.settings_button.setToolTip("Configuración y modo desarrollador")
        self.quick_microphone_button.setToolTip("Activar o desactivar escucha")
        self.close_button = QPushButton("×")
        self.close_button.setToolTip("Cerrar Ámbar")
        self.settings_button.clicked.connect(self.show_settings)
        self.quick_microphone_button.clicked.connect(self.toggle_microphone)
        self.close_button.clicked.connect(self.close)

        self.resize_grip = QSizeGrip(self)
        self._build_settings_panel()

        header = QHBoxLayout()
        header.addStretch()
        header.addWidget(self.quick_microphone_button)
        header.addWidget(self.settings_button)
        header.addWidget(self.close_button)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addStretch()
        layout.addWidget(self.avatar, 1)
        for widget in (self.name, self.status, self.mode_status, self.transcript):
            layout.addWidget(widget)
        layout.addWidget(self.resize_grip, alignment=Qt.AlignRight)
        layout.addStretch()
        self.setLayout(layout)
        self.quick_microphone_button.setVisible(self._show_microphone_button)
        self._set_developer_controls_visible(False)

    def _build_settings_panel(self):
        self.settings_panel = QDialog(self)
        self.settings_panel.setWindowTitle("Configuración de Ámbar")
        self.settings_panel.setModal(False)
        self.settings_panel.setMinimumWidth(300)

        self.show_microphone_checkbox = QCheckBox("Mostrar botón de micrófono")
        self.show_microphone_checkbox.setChecked(self._show_microphone_button)
        self.developer_mode_button = QPushButton("Modo desarrollador: desactivado")
        self.microphone_button = QPushButton("Micrófono: apagado")
        self.transcribe_button = QPushButton("Transcribir")
        self.finish_button = QPushButton("Finalizar")
        self.transcribe_button.setEnabled(False)

        self.show_microphone_checkbox.toggled.connect(self.set_show_microphone_button)
        self.developer_mode_button.clicked.connect(self.toggle_developer_mode)
        self.microphone_button.clicked.connect(self.toggle_microphone)
        self.transcribe_button.clicked.connect(self.toggle_transcription)
        self.finish_button.clicked.connect(self.finish_test)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Controles"))
        layout.addWidget(self.show_microphone_checkbox)
        layout.addWidget(QLabel("Modo desarrollador"))
        layout.addWidget(self.developer_mode_button)
        layout.addWidget(self.microphone_button)
        layout.addWidget(self.transcribe_button)
        layout.addWidget(self.finish_button)
        self.settings_panel.setLayout(layout)

    def show_settings(self):
        self.settings_panel.show()
        self.settings_panel.raise_()
        self.settings_panel.activateWindow()

    def set_show_microphone_button(self, visible):
        self._show_microphone_button = bool(visible)
        self._settings.setValue("ui/show_microphone_button", self._show_microphone_button)
        self.quick_microphone_button.setVisible(self._show_microphone_button)

    def set_system_state(self, state):
        self.avatar.set_system_state(state)
        self.status.setText(self._DISPLAY[state])

    def set_test_state(self, state):
        if state == "listening":
            self.avatar.set_expression("listening")
            self.status.setText("Prueba: hablando...")
            self.transcript.setText("")
        elif state == "thinking":
            self.avatar.set_expression("thinking")
            self.status.setText("Transcribiendo prueba...")

    def set_microphone_enabled(self, enabled):
        self._microphone_enabled = enabled
        self.microphone_button.setText(f"Micrófono: {'encendido' if enabled else 'apagado'}")
        self.transcribe_button.setEnabled(enabled)
        if not enabled:
            self._transcription_active = False
            self.transcribe_button.setText("Transcribir")

    def set_mode_status(self, mode, casual):
        self.mode_status.setText(f"MODO: {mode.upper()} • CASUAL: {'ACTIVADO' if casual else 'DESACTIVADO'}")

    def toggle_microphone(self):
        enabled = not self._microphone_enabled
        if not enabled and self._transcription_active:
            self._events.emit("gui.test.stop")
        self._events.emit("gui.microphone.set", enabled)
        if enabled:
            self._transcription_active = True
            self.start_test()

    def toggle_developer_mode(self):
        self._developer_mode = not self._developer_mode
        self._set_developer_controls_visible(self._developer_mode)
        if self._developer_mode:
            self.developer_mode_button.setText("Modo desarrollador: activado")
            self._events.emit("gui.microphone.set", False)
        else:
            self.developer_mode_button.setText("Modo desarrollador: desactivado")
            if self._transcription_active:
                self.stop_test()
            self._transcription_active = False
            self._events.emit("gui.microphone.set", True)

    def _set_developer_controls_visible(self, visible):
        for widget in (self.microphone_button, self.transcribe_button, self.finish_button):
            widget.setVisible(visible)

    def finish_test(self):
        if self._transcription_active:
            self._transcription_active = False
            self.transcribe_button.setText("Transcribir")
            self.stop_test()
        self._events.emit("gui.microphone.set", False)

    def toggle_transcription(self):
        if not self._transcription_active:
            self._transcription_active = True
            self.transcribe_button.setText("Finalizar y transcribir")
            self.start_test()
        else:
            self._transcription_active = False
            self.transcribe_button.setText("Transcribir")
            self.stop_test()

    def start_test(self):
        self.set_test_state("listening")
        self._events.emit("gui.test.start")

    def stop_test(self):
        self.set_test_state("thinking")
        self._events.emit("gui.test.stop")

    def set_transcript(self, text):
        self.transcript.setText(f"Escuché: {text}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        event.accept()

    def closeEvent(self, event):
        self._settings.setValue("window/geometry", self.saveGeometry())
        if self._transcription_active:
            self._events.emit("gui.test.stop")
        self.settings_panel.close()
        event.accept()
