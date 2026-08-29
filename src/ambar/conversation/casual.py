"""Control de iniciativas casuales, sin timers ni hilos propios."""

import random
import time


class CasualController:
    """Decide si una iniciativa ocasional es admisible en esta sesión."""

    def __init__(self, settings=None, clock=time.monotonic, random_source=None):
        settings = settings or {}
        self._sleep_seconds = float(settings.get("sleep_seconds", 30))
        self._cooldown_seconds = float(settings.get("cooldown_seconds", 300))
        self._jitter_seconds = float(settings.get("jitter_seconds", 20))
        self._clock = clock
        self._random = random_source or random.Random()
        self.enabled = False
        self.in_progress = False
        self._next_due = float("inf")

    def enable(self, mode_name):
        if mode_name != "normal":
            return False
        self.enabled = True
        self.record_activity()
        return True

    def disable(self):
        self.enabled = False
        self.in_progress = False
        self._next_due = float("inf")

    def shutdown(self):
        self.disable()

    def record_activity(self):
        # Sólo un período continuo de sueño habilita una iniciativa. Mientras
        # el usuario está activo no queda ninguna cita casual pendiente.
        self._next_due = float("inf")

    def on_sleep(self):
        """Programa la iniciativa sólo cuando Ámbar ya está dormida."""
        if self.enabled:
            self._next_due = self._clock() + self._sleep_seconds + self._jitter()

    def on_mode_changed(self, mode_name):
        if mode_name != "normal":
            self.disable()

    def begin_if_due(self, mode_name, *, sleeping, busy):
        if (
            not self.enabled
            or self.in_progress
            or mode_name != "normal"
            or not sleeping
            or busy
            or self._clock() < self._next_due
        ):
            return False
        self.in_progress = True
        # Reservar el siguiente intervalo antes de generar evita duplicados
        # aunque el proveedor tarde o falle.
        self._next_due = self._clock() + self._cooldown_seconds + self._jitter()
        return True

    def complete(self):
        self.in_progress = False

    def _jitter(self):
        return self._random.uniform(0, max(0, self._jitter_seconds))
