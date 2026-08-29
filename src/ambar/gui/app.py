from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from ambar.core.state_manager import StateManager
from ambar.gui.window import AmberWindow


class _StateBridge(QObject):
    changed = Signal(object)
    test_state = Signal(str)
    transcript = Signal(str)
    microphone_changed = Signal(bool)
    mode_changed = Signal(str, bool)


class AmberGUI:
    def __init__(self, events):
        self._events = events
        self._closed = False
        self.app = QApplication.instance() or QApplication([])
        self.window = AmberWindow(events)
        self._bridge = _StateBridge()
        self._bridge.changed.connect(self.window.set_system_state)
        self._bridge.test_state.connect(self.window.set_test_state)
        self._bridge.transcript.connect(self.window.set_transcript)
        self._bridge.microphone_changed.connect(self.window.set_microphone_enabled)
        self._bridge.mode_changed.connect(self.window.set_mode_status)
        events.subscribe(StateManager.EVENT_NAME, self._on_state_changed)
        events.subscribe("gui.test.state", self._on_test_state)
        events.subscribe("gui.test.transcript", self._on_transcript)
        events.subscribe("gui.microphone.changed", self._on_microphone_changed)
        events.subscribe("mode.changed", self._on_mode_changed)
        events.subscribe("casual.changed", self._on_casual_changed)

    def _on_state_changed(self, data):
        if not self._closed:
            self._bridge.changed.emit(data["current"])

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
        self._events.unsubscribe(StateManager.EVENT_NAME, self._on_state_changed)
        self._events.unsubscribe("gui.test.state", self._on_test_state)
        self._events.unsubscribe("gui.test.transcript", self._on_transcript)
        self._events.unsubscribe("gui.microphone.changed", self._on_microphone_changed)
        self._events.unsubscribe("mode.changed", self._on_mode_changed)
        self._events.unsubscribe("casual.changed", self._on_casual_changed)
        for signal in (
            self._bridge.changed,
            self._bridge.test_state,
            self._bridge.transcript,
            self._bridge.microphone_changed,
            self._bridge.mode_changed,
        ):
            try:
                signal.disconnect()
            except RuntimeError:
                pass
