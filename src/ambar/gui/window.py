from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizeGrip, QVBoxLayout, QWidget
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
        super().__init__(); self._events = events; self._settings = QSettings("AMBAR", "AMBAR")
        self._drag_offset = None; self._microphone_enabled = self._transcription_active = self._developer_mode = False
        self.setWindowTitle("Ámbar"); self.setMinimumSize(280, 320); self.resize(340, 390)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint); self.restoreGeometry(self._settings.value("window/geometry", b""))
        self.avatar = AvatarWidget(); self.name, self.status = QLabel("ÁMBAR"), QLabel("Dormida")
        self.mode_status, self.transcript = QLabel("MODO: NORMAL • CASUAL: DESACTIVADO"), QLabel("")
        for label in (self.name, self.status, self.mode_status, self.transcript):
            label.setAlignment(Qt.AlignCenter); label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.transcript.setWordWrap(True)
        self.developer_mode_button, self.microphone_button = QPushButton("Modo pruebas: desactivado"), QPushButton("Micrófono: apagado")
        self.transcribe_button, self.finish_button, self.exit_button = QPushButton("Transcribir"), QPushButton("Finalizar"), QPushButton("Salir")
        self.resize_grip = QSizeGrip(self); self.transcribe_button.setEnabled(False)
        self.developer_mode_button.clicked.connect(self.toggle_developer_mode); self.microphone_button.clicked.connect(self.toggle_microphone)
        self.transcribe_button.clicked.connect(self.toggle_transcription); self.finish_button.clicked.connect(self.finish_test); self.exit_button.clicked.connect(self.close)
        controls = QHBoxLayout()
        for button in (self.developer_mode_button, self.microphone_button, self.transcribe_button, self.finish_button, self.exit_button): controls.addWidget(button)
        layout = QVBoxLayout(); layout.addStretch(); layout.addWidget(self.avatar, 1)
        for widget in (self.name, self.status, self.mode_status, self.transcript): layout.addWidget(widget)
        layout.addLayout(controls); layout.addWidget(self.resize_grip, alignment=Qt.AlignRight); layout.addStretch(); self.setLayout(layout)
        self._set_developer_controls_visible(False)
    def set_system_state(self, state): self.avatar.set_system_state(state); self.status.setText(self._DISPLAY[state])
    def set_test_state(self, state):
        if state == "listening": self.avatar.set_expression("listening"); self.status.setText("Prueba: hablando..."); self.transcript.setText("")
        elif state == "thinking": self.avatar.set_expression("thinking"); self.status.setText("Transcribiendo prueba...")
    def set_microphone_enabled(self, enabled):
        self._microphone_enabled = enabled; self.microphone_button.setText(f"Micrófono: {'encendido' if enabled else 'apagado'}"); self.transcribe_button.setEnabled(enabled)
        if not enabled: self._transcription_active = False; self.transcribe_button.setText("Transcribir")
    def set_mode_status(self, mode, casual): self.mode_status.setText(f"MODO: {mode.upper()} • CASUAL: {'ACTIVADO' if casual else 'DESACTIVADO'}")
    def toggle_microphone(self):
        enabled = not self._microphone_enabled
        if not enabled and self._transcription_active: self._events.emit("gui.test.stop")
        self._events.emit("gui.microphone.set", enabled)
        if enabled: self._transcription_active = True; self.start_test()
    def toggle_developer_mode(self):
        self._developer_mode = not self._developer_mode; self._set_developer_controls_visible(self._developer_mode)
        if self._developer_mode: self.developer_mode_button.setText("Modo pruebas: activado"); self._events.emit("gui.microphone.set", False)
        else:
            self.developer_mode_button.setText("Modo pruebas: desactivado")
            if self._transcription_active: self.stop_test()
            self._transcription_active = False; self._events.emit("gui.microphone.set", True)
    def _set_developer_controls_visible(self, visible):
        for widget in (self.microphone_button, self.transcribe_button, self.finish_button): widget.setVisible(visible)
    def finish_test(self):
        if self._transcription_active: self._transcription_active = False; self.transcribe_button.setText("Transcribir"); self.stop_test()
        self._events.emit("gui.microphone.set", False)
    def toggle_transcription(self):
        if not self._transcription_active: self._transcription_active = True; self.transcribe_button.setText("Finalizar y transcribir"); self.start_test()
        else: self._transcription_active = False; self.transcribe_button.setText("Transcribir"); self.stop_test()
    def start_test(self): self.set_test_state("listening"); self._events.emit("gui.test.start")
    def stop_test(self): self.set_test_state("thinking"); self._events.emit("gui.test.stop")
    def set_transcript(self, text): self.transcript.setText(f"Escuché: {text}")
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft(); event.accept()
    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton: self.move(event.globalPosition().toPoint() - self._drag_offset); event.accept()
    def mouseReleaseEvent(self, event): self._drag_offset = None; event.accept()
    def closeEvent(self, event):
        self._settings.setValue("window/geometry", self.saveGeometry())
        if self._transcription_active: self._events.emit("gui.test.stop")
        event.accept()
