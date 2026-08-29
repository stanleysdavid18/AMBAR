from collections import defaultdict
import logging
import threading


class EventBus:
    """
    Bus de eventos de Ámbar.

    Permite que los módulos se comuniquen
    sin depender unos de otros.
    """

    def __init__(self):
        self._listeners = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(self, event_name, callback):
        """
        Registra un listener para un evento.
        """
        with self._lock:
            if callback not in self._listeners[event_name]:
                self._listeners[event_name].append(callback)
        return lambda: self.unsubscribe(event_name, callback)

    def unsubscribe(self, event_name, callback):
        with self._lock:
            listeners = self._listeners.get(event_name, [])
            if callback in listeners:
                listeners.remove(callback)

    def emit(self, event_name, data=None):
        """
        Dispara un evento.
        """

        with self._lock:
            callbacks = tuple(self._listeners.get(event_name, ()))
        for callback in callbacks:
            try:
                callback(data)
            except Exception:
                logging.getLogger(__name__).exception("Error delivering event %s", event_name)
