from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from ambar.core.state import SystemState
from ambar.core.state_manager import StateManager
from ambar.gui.first_run import FirstRunWizard
from ambar.gui.window import AmberWindow


class _StateBridge(QObject):
    changed = Signal(object)
    test_state = Signal(str)
    transcript = Signal(str)
    microphone_changed = Signal(bool)
    mode_changed = Signal(str, bool)
    teach_app_requested = Signal(object)
    wake_detected = Signal()


class AmberGUI:
    def __init__(self, events):
        self._events = events
        self._closed = False
        self._exiting = False
        self.app = QApplication.instance() or QApplication([])
        self.app.setQuitOnLastWindowClosed(False)
        self._show_first_run_wizard()
        self.window = AmberWindow(events)
        self._bridge = _StateBridge()
        self._bridge.changed.connect(self.window.set_system_state)
        self._bridge.test_state.connect(self.window.set_test_state)
        self._bridge.transcript.connect(self.window.set_transcript)
        self._bridge.microphone_changed.connect(self.window.set_microphone_enabled)
        self._bridge.mode_changed.connect(self.window.set_mode_status)
        self._bridge.teach_app_requested.connect(self.window.show_teach_app_dialog)
        self._bridge.wake_detected.connect(self.restore_window)
        self.window.minimized_to_tray.connect(self._show_tray_hint)
        self.window.exit_requested.connect(self.exit_application)
        self._create_tray()

        events.subscribe(StateManager.EVENT_NAME, self._on_state_changed)
        events.subscribe("gui.test.state", self._on_test_state)
        events.subscribe("gui.test.transcript", self._on_transcript)
        events.subscribe("gui.microphone.changed", self._on_microphone_changed)
        events.subscribe("mode.changed", self._on_mode_changed)
        events.subscribe("casual.changed", self._on_casual_changed)
        events.subscribe("gui.teach_app.request", self._on_teach_app_request)

    def _show_first_run_wizard(self):
        settings = QSettings("AMBAR", "AMBAR")
        if not settings.value("onboarding/completed", False, type=bool):
            FirstRunWizard().exec()

    def _create_tray(self):
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self.app)
        self.tray.setToolTip("Ámbar")
        self.tray_menu = QMenu()
        self.show_action = QAction("Mostrar Ámbar", self.tray_menu)
        self.exit_action = QAction("Salir", self.tray_menu)
        self.show_action.triggered.connect(self.restore_window)
        self.exit_action.triggered.connect(self.exit_application)
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.restore_window()

    def _show_tray_hint(self):
        self.tray.showMessage("Ámbar", "Ámbar sigue activa y escuchando en segundo plano.")

    def restore_window(self):
        if self._exiting:
            return
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    def exit_application(self):
        self._exiting = True
        self.window.allow_exit()
        self.tray.hide()
        self.app.quit()

    def _on_state_changed(self, data):
        if not self._closed:
            self._bridge.changed.emit(data["current"])
            if (
                data.get("previous") is SystemState.SLEEPING
                and data.get("current") is SystemState.LISTENING
            ):
                self._bridge.wake_detected.emit()

    def _on_test_state(self, state):
        if not self._closed:
            self._bridge.test_state.emit(state)

    def _on_transcript(self, text):
        if not self._closed:
            self._bridge.transcript.emit(text)

    def _on_microphone_changed(self, enabled):
        if not self._closed:
            self._bridge.microphone_changed.emit(enabled)

    def _on_mode_changed(self, data):
        if not self._closed:
            self._bridge.mode_changed.emit(data["mode"], bool(data.get("casual")))

    def _on_teach_app_request(self, data):
        if not self._closed:
            self._bridge.teach_app_requested.emit(data)

    def _on_casual_changed(self, enabled):
        if not self._closed:
            self._bridge.mode_changed.emit("normal", enabled)

    def run(self):
        self.window.show()
        self.app.exec()

    def shutdown(self):
        """Disconnect event callbacks before Qt tears down its objects."""
        if self._closed:
            return
        self._closed = True
        self.tray.hide()
        self._events.unsubscribe(StateManager.EVENT_NAME, self._on_state_changed)
        self._events.unsubscribe("gui.test.state", self._on_test_state)
        self._events.unsubscribe("gui.test.transcript", self._on_transcript)
        self._events.unsubscribe("gui.microphone.changed", self._on_microphone_changed)
        self._events.unsubscribe("mode.changed", self._on_mode_changed)
        self._events.unsubscribe("casual.changed", self._on_casual_changed)
        self._events.unsubscribe("gui.teach_app.request", self._on_teach_app_request)
        for signal in (
            self._bridge.changed,
            self._bridge.test_state,
            self._bridge.transcript,
            self._bridge.microphone_changed,
            self._bridge.mode_changed,
            self._bridge.teach_app_requested,
            self._bridge.wake_detected,
        ):
            try:
                signal.disconnect()
            except RuntimeError:
                pass






