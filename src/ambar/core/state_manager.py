from ambar.core.state import SystemState
import threading


class StateManager:
    """Fuente única del estado observable de Ámbar."""

    EVENT_NAME = "system.state_changed"

    def __init__(self, events):
        self._events = events
        self._state = SystemState.OFFLINE
        self._lock = threading.RLock()

    @property
    def current(self):
        with self._lock:
            return self._state

    def set(self, state):
        if not isinstance(state, SystemState):
            raise TypeError("state debe ser una instancia de SystemState")
        with self._lock:
            if state == self._state:
                return
            previous = self._state
            self._state = state
        self._events.emit(self.EVENT_NAME, {"previous": previous, "current": state})
