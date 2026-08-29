import threading
import time
import unicodedata
import re

from ambar.core.state import SystemState
from ambar.config.manager import ConfigManager
from ambar.conversation.casual import CasualController


class ConversationService:
    """Coordina una sesión de voz sin conocer detalles de GUI o hardware."""

    def __init__(self, brain, voice, states, events, casual=None):
        self._brain, self._voice = brain, voice
        self._states, self._events = states, events
        self._running, self._sleeping = False, True
        self._test_requested = False
        self._test_stop_event = threading.Event()
        # El contador inicia al finalizar la respuesta, no antes de que el
        # modelo y Piper terminen su trabajo.
        config = ConfigManager()
        self._idle_timeout_seconds = config.get("conversation", "sleep_idle_seconds")
        self._last_activity = time.monotonic()
        self._casual = casual or CasualController(config.get("casual"))
        events.subscribe("gui.test.start", self._request_test)
        events.subscribe("gui.test.stop", self._stop_test)

    def start(self):
        self._running, self._sleeping = True, True
        self._last_activity = time.monotonic()
        self._states.set(SystemState.SLEEPING)
        if self._voice.start() is False:
            self._report_error("No se pudo iniciar el micrófono.")
        while self._running:
            if self._test_requested:
                self._run_test()
                continue
            message = self._voice.next_message(timeout=0.25)
            if message:
                if not self._voice.pause_listening():
                    self._states.set(SystemState.ERROR)
                    continue
                try:
                    self.handle(message)
                except Exception as error:
                    self._report_error("No pude procesar tu solicitud.", error)
                if self._running and not self._sleeping:
                    if self._voice.resume_listening() is False:
                        self._report_error("No se pudo reactivar el micrófono.")
                    else:
                        self._states.set(SystemState.LISTENING)
            elif (
                not self._sleeping
                and time.monotonic() - self._last_activity >= self._idle_timeout_seconds
            ):
                print("[Conversacion] Sin actividad. Ambar se duerme.")
                self._sleeping = True
                self._states.set(SystemState.SLEEPING)
                self._casual.on_sleep()
            else:
                self._try_casual_interaction()
        self._voice.stop()
        self._casual.shutdown()
        self._states.set(SystemState.OFFLINE)

    def stop(self):
        self._running = False
        self._test_stop_event.set()
        self._casual.shutdown()

    def _request_test(self, _data=None):
        if not self._test_requested:
            self._test_stop_event.clear()
            self._test_requested = True

    def _stop_test(self, _data=None):
        self._test_stop_event.set()

    def _run_test(self):
        self._test_requested = False
        if self._voice.pause_listening() is False:
            self._report_error("No se pudo pausar el micrófono.")
            return
        self._states.set(SystemState.LISTENING)
        self._events.emit("gui.test.state", "listening")
        try:
            text = self._voice.listen_until(self._test_stop_event)
        except Exception as error:
            self._report_error("No pude transcribir la prueba.", error)
            text = ""
        self._states.set(SystemState.THINKING)
        self._events.emit("gui.test.state", "thinking")
        self._events.emit("gui.test.transcript", text or "No se detectó voz.")
        if text:
            self.handle(text)
        if self._running and not self._sleeping:
            self._voice.resume_listening()
        elif not text:
            self._states.set(SystemState.SLEEPING)

    def handle(self, message):
        message = message.strip()
        if not message:
            return
        self._casual.record_activity()
        self._events.emit("conversation.user_message", message)
        self._last_activity = time.monotonic()
        if self._sleeping:
            if self._voice.is_wake_word(message):
                print(f"[Conversación] Activación detectada: {message!r}")
                self._sleeping = False
                self._states.set(SystemState.LISTENING)
                command_after_wake = self._without_wake_word(message)
                if command_after_wake:
                    self.handle(command_after_wake)
                    return
                self._respond(self._brain.wake_greeting())
                if self._running and not self._sleeping:
                    self._states.set(SystemState.LISTENING)
            return
        if self._voice.is_wake_word(message):
            message = self._without_wake_word(message)
            if not message:
                self._respond("Sí, dime.")
                return
        if self._handle_casual_command(message):
            return
        command = self._normalize(message)
        if command == "salir":
            self._respond("Hasta luego.")
            self.stop()
            return
        if command in {
            "duerme", "duermete", "a dormir", "vete a dormir",
            "descansa", "adios", "apagate",
        }:
            self._respond("Hasta luego.")
            self._sleeping = True
            self._states.set(SystemState.SLEEPING)
            self._casual.on_sleep()
            return
        self._states.set(SystemState.THINKING)
        previous_mode = self._mode_name()
        try:
            response = self._brain.think(message)
        except Exception as error:
            self._report_error("No puedo conectarme con el motor de IA.", error)
            return
        self._respond(response.text, response.speak)
        current_mode = self._mode_name()
        if current_mode != previous_mode:
            self._casual.on_mode_changed(current_mode)
            self._events.emit("mode.changed", {"mode": current_mode, "casual": self._casual.enabled})
        for action in response.actions:
            try:
                action.execute()
            except Exception as error:
                self._report_error("No pude ejecutar esa acción.", error)
        if self._running and not self._sleeping:
            self._states.set(SystemState.LISTENING)

    def _respond(self, text, speak=True):
        self._events.emit("conversation.assistant_response", text)
        if speak:
            self._states.set(SystemState.SPEAKING)
            try:
                interruption = self._voice.speak(text)
                if interruption:
                    self._events.emit("conversation.interrupted", interruption)
                    self.handle(interruption)
            except Exception as error:
                self._report_error("No pude reproducir la respuesta.", error)
        self._last_activity = time.monotonic()

    def _report_error(self, user_message, error=None):
        if error:
            print(f"[Conversation] {user_message} Detail: {error}")
        self._states.set(SystemState.ERROR)
        self._events.emit("conversation.error", user_message)

    def _handle_casual_command(self, message):
        command = self._normalize(message)
        if "modo casual" not in command:
            return False

        mode = self._mode_name()
        if "desactiva" in command or "desactivar" in command:
            self._casual.disable()
            self._events.emit("casual.changed", False)
            self._respond("Listo, vuelvo al modo normal.")
            return True
        if "activa" in command or "activar" in command or "quiero" in command:
            if not self._casual.enable(mode):
                self._respond("El modo casual solo está disponible en modo normal.")
                return True
            self._events.emit("casual.changed", True)
            self._events.emit("mode.changed", {"mode": mode, "casual": True})
            self._respond("Listo. Modo casual activado.")
            return True
        return False

    def _try_casual_interaction(self):
        """Ejecuta como máximo una iniciativa cuando el bucle está inactivo."""
        mode = self._mode_name()
        busy = self._states.current in {SystemState.THINKING, SystemState.SPEAKING}
        if not self._casual.begin_if_due(mode, sleeping=self._sleeping, busy=busy):
            return
        try:
            self._states.set(SystemState.THINKING)
            text = self._brain.casual_prompt()
            if text:
                self._respond(text)
                # Una respuesta del usuario a esta iniciativa continúa la
                # conversación normal sin exigir otra palabra de activación.
                self._sleeping = False
        except Exception as error:
            self._report_error("No pude iniciar una interacción casual.", error)
        finally:
            self._casual.complete()
            if self._running:
                self._states.set(SystemState.LISTENING if not self._sleeping else SystemState.SLEEPING)

    def _mode_name(self):
        manager = getattr(self._brain, "mode_manager", None)
        return manager.current_name() if manager else "normal"

    @staticmethod
    def _without_wake_word(text):
        return re.sub(r"^\s*(?:(?:hola|oye)\s+)?[áa]mbar[,:¡!\s]*", "", text, flags=re.I).strip()

    @staticmethod
    def _normalize(text):
        normalized = unicodedata.normalize("NFD", text.casefold())
        return "".join(char for char in normalized if not unicodedata.combining(char))
