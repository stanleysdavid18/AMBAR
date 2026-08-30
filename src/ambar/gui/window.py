from PySide6.QtCore import QEvent, QSettings, QTimer, Qt, Signal
import sounddevice as sd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QLabel,
    QPushButton,
    QSizeGrip,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from ambar.config.manager import ConfigManager
from ambar.config.secrets import ApiKeyStore
from ambar.core.state import SystemState
from ambar.gui.avatar import AvatarWidget


class AmberWindow(QWidget):
    minimized_to_tray = Signal()
    exit_requested = Signal()
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
        self._key_store = ApiKeyStore()
        self._drag_offset = None
        self._allow_exit = False
        self._show_microphone_button = self._settings.value("ui/show_microphone_button", True, type=bool)
        self._microphone_enabled = self._transcription_active = self._developer_mode = False

        self.setWindowTitle("Ámbar betaV2")
        self.setMinimumSize(280, 320)
        self.resize(340, 390)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.setStyleSheet("QWidget { background: #140f1f; color: #f7efff; font-family: Segoe UI; } QPushButton { background: #342547; border: 1px solid #795ca0; border-radius: 12px; padding: 7px 10px; } QPushButton:hover { background: #4b3565; } QLabel { color: #eadcf7; }")
        self.restoreGeometry(self._settings.value("window/geometry", b""))

        self.avatar = AvatarWidget()
        self.name = QLabel("ÁMBAR • betaV2")
        self.status = QLabel("Dormida")
        self.mode_status = QLabel("MODO: NORMAL • CASUAL: DESACTIVADO")
        self.transcript = QLabel("")
        for label in (self.name, self.status, self.mode_status, self.transcript):
            label.setAlignment(Qt.AlignCenter)
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.transcript.setWordWrap(True)

        self.parameters_button = QPushButton("(/)")
        self.settings_button = QPushButton("⚙️")
        self.quick_microphone_button = QPushButton("🎤")
        self.parameters_button.setToolTip("Parámetros de voz")
        self.settings_button.setToolTip("Configuración y modo desarrollador")
        self.quick_microphone_button.setToolTip("Activar o desactivar escucha")
        self.minimize_button = QPushButton("—")
        self.minimize_button.setToolTip("Minimizar a la bandeja")
        self.close_button = QPushButton("×")
        self.close_button.setToolTip("Cerrar Ámbar")
        self.parameters_button.clicked.connect(self.show_voice_parameters)
        self.settings_button.clicked.connect(self.show_settings)
        self.quick_microphone_button.clicked.connect(self.toggle_microphone)
        self.minimize_button.clicked.connect(self.minimize_to_tray)
        self.close_button.clicked.connect(self.exit_requested.emit)

        self.resize_grip = QSizeGrip(self)
        self._build_settings_panel()
        self._build_voice_parameters_dialog()

        header = QHBoxLayout()
        header.addStretch()
        header.addWidget(self.quick_microphone_button)
        header.addWidget(self.parameters_button)
        header.addWidget(self.settings_button)
        header.addWidget(self.minimize_button)
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

    _VOICE_PRESETS = {
        "Bajo": {"min_threshold": 0.015, "noise_multiplier": 2.5, "max_threshold": 0.05, "barge_in_threshold": 0.015},
        "Medio": {"min_threshold": 0.008, "noise_multiplier": 2.0, "max_threshold": 0.03, "barge_in_threshold": 0.006},
        "Alto": {"min_threshold": 0.004, "noise_multiplier": 1.5, "max_threshold": 0.02, "barge_in_threshold": 0.003},
    }

    def _build_voice_parameters_dialog(self):
        voice = ConfigManager().get("voice")
        self.voice_parameters_dialog = QDialog(self)
        self.voice_parameters_dialog.setWindowTitle("Parámetros de voz")
        layout = QVBoxLayout(self.voice_parameters_dialog)
        self.parameters_switch = QPushButton("Switch: modo simple")
        self.parameters_switch.clicked.connect(self.toggle_parameters_mode)
        layout.addWidget(self.parameters_switch)

        self.simple_parameters = QWidget()
        simple_layout = QFormLayout(self.simple_parameters)
        self.voice_preset = QComboBox()
        self.voice_preset.addItems(("Bajo", "Medio", "Alto"))
        self.voice_preset.setCurrentText("Medio")
        self.preset_explanation = QLabel()
        self.preset_explanation.setWordWrap(True)
        self.voice_preset.currentTextChanged.connect(self._update_preset_explanation)
        simple_layout.addRow("Umbral", self.voice_preset)
        simple_layout.addRow(self.preset_explanation)
        layout.addWidget(self.simple_parameters)

        self.manual_parameters = QWidget()
        form = QFormLayout(self.manual_parameters)
        self._voice_fields = {}
        definitions = (
            ("record_max_seconds", "Máximo de grabación (s)", 1.0, 120.0, 1),
            ("silence_seconds", "Silencio para finalizar (s)", 0.2, 10.0, 1),
            ("min_threshold", "Umbral mínimo", 0.001, 0.1, 3),
            ("noise_multiplier", "Multiplicador de ruido", 1.0, 5.0, 2),
            ("max_threshold", "Umbral máximo", 0.005, 0.2, 3),
            ("barge_in_max_seconds", "Escucha durante habla (s)", 1.0, 15.0, 1),
            ("barge_in_threshold", "Umbral durante habla", 0.001, 0.1, 3),
        )
        for key, label, minimum, maximum, decimals in definitions:
            field = QDoubleSpinBox()
            field.setRange(minimum, maximum)
            field.setDecimals(decimals)
            field.setSingleStep(0.1 if decimals == 1 else 0.001)
            field.setValue(float(voice.get(key, minimum)))
            self._voice_fields[key] = field
            form.addRow(label, field)
        self.barge_in_checkbox = QCheckBox("Permitir interrupción mientras Ámbar habla")
        self.barge_in_checkbox.setChecked(bool(voice.get("barge_in_enabled", True)))
        form.addRow(self.barge_in_checkbox)
        layout.addWidget(self.manual_parameters)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_voice_parameters)
        buttons.rejected.connect(self.voice_parameters_dialog.reject)
        layout.addWidget(buttons)
        self._simple_parameters_mode = True
        self.manual_parameters.setVisible(False)
        self._update_preset_explanation(self.voice_preset.currentText())

    def toggle_parameters_mode(self):
        self._simple_parameters_mode = not self._simple_parameters_mode
        self.simple_parameters.setVisible(self._simple_parameters_mode)
        self.manual_parameters.setVisible(not self._simple_parameters_mode)
        self.parameters_switch.setText(
            "Switch: modo manual" if self._simple_parameters_mode else "Switch: modo simple"
        )

    def _update_preset_explanation(self, preset):
        explanations = {
            "Bajo": "Bajo: requiere una voz más fuerte. Reduce activaciones por ruido o eco.",
            "Medio": "Medio: equilibrio recomendado para la mayoría de micrófonos.",
            "Alto": "Alto: escucha voces más suaves, pero puede captar más ruido ambiental.",
        }
        self.preset_explanation.setText(explanations[preset])

    def show_voice_parameters(self):
        self.voice_parameters_dialog.show()
        self.voice_parameters_dialog.raise_()
        self.voice_parameters_dialog.activateWindow()

    def save_voice_parameters(self):
        values = {key: field.value() for key, field in self._voice_fields.items()}
        if self._simple_parameters_mode:
            values.update(self._VOICE_PRESETS[self.voice_preset.currentText()])
        values["barge_in_enabled"] = self.barge_in_checkbox.isChecked()
        ConfigManager().update_section("voice", values)
        self._events.emit("voice.settings.changed", values)
        self.voice_parameters_dialog.accept()
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
        self.api_key_fields = {}
        self.api_keys_form = QFormLayout()
        for key_name in ApiKeyStore.KEY_NAMES:
            field = QLineEdit()
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setPlaceholderText(ApiKeyStore.mask(self._key_store.get(key_name)))
            self.api_key_fields[key_name] = field
            self.api_keys_form.addRow(key_name, field)
        self.save_api_keys_button = QPushButton("Guardar API Keys")
        self.api_keys_status = QLabel("")
        self.dev_testing_checkbox = QCheckBox("Activar modo pruebas del desarrollador")
        self.dev_risks_checkbox = QCheckBox("Entiendo los riesgos")
        self.dev_risks_checkbox.setEnabled(False)
        self.dev_warning = QLabel(
            "Opción experimental solo para pruebas. Puede no funcionar, tiene límites, no es el modo recomendado para usuarios finales y puede dejar de estar disponible."
        )
        self.dev_warning.setWordWrap(True)
        self.dev_warning.setStyleSheet("color: #ffcf7a;")
        self.google_dev_button = QPushButton("Continuar con Google (pruebas)")
        self.dev_testing_status = QLabel("")
        self.dev_testing_checkbox.toggled.connect(self._prepare_dev_testing)
        self.dev_risks_checkbox.toggled.connect(self._set_dev_testing)
        self.google_dev_button.clicked.connect(self.show_google_dev_notice)
        saved_dev_mode = self._settings.value("developer/testing_mode", False, type=bool)
        self.dev_testing_checkbox.setChecked(saved_dev_mode)
        self.dev_risks_checkbox.setEnabled(saved_dev_mode)
        self.dev_risks_checkbox.setChecked(saved_dev_mode)
        if saved_dev_mode:
            self._set_dev_testing(True)
        self.save_api_keys_button.clicked.connect(self.save_api_keys)

        self._input_devices = [
            (index, device["name"])
            for index, device in enumerate(sd.query_devices())
            if device.get("max_input_channels", 0) > 0
        ]
        if len(self._input_devices) > 1:
            self.microphone_selector = QComboBox()
            for index, name in self._input_devices:
                self.microphone_selector.addItem(name, index)
            selected = ConfigManager().get("voice").get("input_device")
            if selected is not None:
                choice = self.microphone_selector.findData(selected)
                if choice >= 0:
                    self.microphone_selector.setCurrentIndex(choice)
            self.microphone_selector.currentIndexChanged.connect(self.set_input_device)
        else:
            self.microphone_selector = None

        self.show_microphone_checkbox.toggled.connect(self.set_show_microphone_button)
        self.developer_mode_button.clicked.connect(self.toggle_developer_mode)
        self.microphone_button.clicked.connect(self.toggle_microphone)
        self.transcribe_button.clicked.connect(self.toggle_transcription)
        self.finish_button.clicked.connect(self.finish_test)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Controles"))
        layout.addWidget(self.show_microphone_checkbox)
        if self.microphone_selector is not None:
            layout.addWidget(QLabel("Micrófono"))
            layout.addWidget(self.microphone_selector)
        layout.addWidget(QLabel("Modo desarrollador"))
        layout.addWidget(self.developer_mode_button)
        layout.addWidget(self.microphone_button)
        layout.addWidget(self.transcribe_button)
        layout.addWidget(self.finish_button)
        layout.addWidget(QLabel("API Keys"))
        layout.addLayout(self.api_keys_form)
        layout.addWidget(self.save_api_keys_button)
        layout.addWidget(self.api_keys_status)
        layout.addWidget(QLabel("Desarrollador / Pruebas (experimental)"))
        layout.addWidget(self.dev_warning)
        layout.addWidget(self.dev_testing_checkbox)
        layout.addWidget(self.dev_risks_checkbox)
        layout.addWidget(self.google_dev_button)
        layout.addWidget(self.dev_testing_status)
        self.settings_panel.setLayout(layout)

    def show_teach_app_dialog(self, data):
        app = (data or {}).get("app", "aplicación")
        command, accepted = QInputDialog.getText(
            self,
            "Enseñar aplicación",
            f"Ruta o comando para {app}:",
        )
        self._events.emit(
            "gui.teach_app.result",
            {"app": app, "command": command, "cancelled": not accepted},
        )
    def show_settings(self):
        self.settings_panel.show()
        self.settings_panel.raise_()
        self.settings_panel.activateWindow()

    def _prepare_dev_testing(self, enabled):
        self.dev_risks_checkbox.setEnabled(enabled)
        if not enabled:
            self.dev_risks_checkbox.setChecked(False)
            self._settings.setValue("developer/testing_mode", False)
            self.dev_testing_status.setText("Modo pruebas desactivado.")
        elif not self.dev_risks_checkbox.isChecked():
            self.dev_testing_status.setText("Confirma que entiendes los riesgos para activar este modo.")

    def _set_dev_testing(self, understood):
        enabled = self.dev_testing_checkbox.isChecked() and understood
        self._settings.setValue("developer/testing_mode", enabled)
        if enabled:
            if ApiKeyStore().dev_secrets_available():
                self.dev_testing_status.setText("Modo pruebas activo.")
            else:
                self.dev_testing_status.setText("Modo pruebas no configurado en este build.")

    def show_google_dev_notice(self):
        # OAuth real requiere client ID, redirect URI y backend para custodiar tokens.
        QMessageBox.information(
            self,
            "Google para pruebas",
            "OAuth de producción no está incluido en este build. Para pruebas, configura config/dev_secrets.json local; no pegues tokens de producción aquí.",
        )
    def save_api_keys(self):
        values = {name: field.text() for name, field in self.api_key_fields.items() if field.text().strip()}
        if not values:
            self.api_keys_status.setText("Escribe al menos una clave para guardar.")
            return
        self._key_store.save(values)
        ConfigManager().update_section("ai", {"mode": "auto"})
        for name, field in self.api_key_fields.items():
            field.clear()
            field.setPlaceholderText(ApiKeyStore.mask(self._key_store.get(name)))
        self.api_keys_status.setText("Claves guardadas localmente.")
    def set_input_device(self, _index):
        if self.microphone_selector is None:
            return
        device = self.microphone_selector.currentData()
        ConfigManager().update_section("voice", {"input_device": device})
        self._events.emit("voice.settings.changed", {"input_device": device})
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

    def minimize_to_tray(self):
        """Oculta la ventana sin detener el motor de conversación."""
        self._settings.setValue("window/geometry", self.saveGeometry())
        self.hide()
        self.minimized_to_tray.emit()

    def allow_exit(self):
        self._allow_exit = True

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.minimize_to_tray)
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
        if self._allow_exit:
            self._settings.setValue("window/geometry", self.saveGeometry())
            if self._transcription_active:
                self._events.emit("gui.test.stop")
            self.settings_panel.close()
            event.accept()
            return
        event.ignore()
        self.minimize_to_tray()





