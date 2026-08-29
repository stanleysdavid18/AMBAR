from ambar.core.state import SystemState
from ambar.voice.background_listener import BackgroundListener
from ambar.voice.listener import Listener
from ambar.voice.speaker import Speaker
from ambar.wakeword import WakeWordDetector
import threading


class VoiceService:
    """
    Única puerta para voz.

    Controla:

    - Escucha continua
    - Síntesis
    - Wake Word

    Nunca debe existir más de una instancia de
    Listener
    Speaker
    BackgroundListener
    """

    def __init__(self, listener=None, speaker=None, wakeword=None, events=None, states=None):

        self._listener = listener
        self._speaker = speaker
        self._wakeword = wakeword or WakeWordDetector()

        self._background_listener = None

        self._listening = False
        self._speaking = False
        # Evita que Piper se recapture por el micrófono durante la reproducción.
        self._barge_in_enabled = False
        # El modo normal siempre inicia con la activación por voz disponible.
        # El modo pruebas puede desactivarlo temporalmente desde la GUI.
        self._microphone_enabled = True
        self._events = events
        self._states = states
        self._lock = threading.RLock()

        if self._events:
            self._events.subscribe("gui.microphone.set", self._set_microphone)

    def _set_microphone(self, enabled):
        self._microphone_enabled = bool(enabled)

        if self._microphone_enabled:
            self.start()
            if self._states:
                self._states.set(SystemState.LISTENING)
        else:
            self.stop()
            if self._states:
                self._states.set(SystemState.SLEEPING)

        if self._events:
            self._events.emit("gui.microphone.changed", self._microphone_enabled)

    # ===========================
    # Escucha continua
    # ===========================

    def start(self):
        with self._lock:
            if not self._microphone_enabled or self._speaking:
                return False
            if self._listening and self._background_listener and self._background_listener.running:
                return self._listening
            self._listening = False
            self._listener = self._listener or Listener()
            self._background_listener = self._background_listener or BackgroundListener(
                self._listener
            )
            self._listening = self._background_listener.start()
            return self._listening

    def stop(self):

        with self._lock:
            if not self._listening:
                return True
            if self._background_listener and not self._background_listener.stop():
                return False
            self._listening = False
            return True

    def pause_listening(self):

        return self.stop()

    def resume_listening(self):
        return self.start()

    @property
    def listening(self):

        return self._listening

    # ===========================
    # Mensajes
    # ===========================

    def next_message(self, timeout=None):

        if not self._background_listener:
            return None

        return self._background_listener.get_message(timeout)

    def listen_until(self, stop_event):

        self._listener = self._listener or Listener()

        return self._listener.listen_until(stop_event)

    # ===========================
    # Voz
    # ===========================

    def speak(self, text):
        """Habla sin permitir que el micrófono capture a Piper como entrada.

        La escucha se restaura en ``finally`` para que un error de síntesis no
        deje a Ámbar muda. No se crea un segundo ``Listener``: ``start``
        reutiliza la instancia ya construida.
        """
        # Mantener el mismo cerrojo durante toda la reproducción evita que un
        # evento de GUI reactive el micrófono a mitad de una frase de Piper.
        with self._lock:
            if self._speaking:
                raise RuntimeError("Ya hay una respuesta de voz en curso.")
            self._speaking = True
            was_listening = self._listening
            if was_listening and not self.pause_listening():
                self._speaking = False
                raise RuntimeError("No se pudo detener el listener antes de hablar.")
            try:
                self._speaker = self._speaker or Speaker()
                if self._barge_in_enabled and hasattr(self._speaker, "synthesize"):
                    return self._speak_with_wake_interruption(text)
                self._speaker.speak(text)
            finally:
                self._speaking = False
                if was_listening and self._microphone_enabled:
                    self.resume_listening()

    def _speak_with_wake_interruption(self, text):
        """Permite cancelar Piper sólo tras oír y transcribir la wake word.

        Se reutiliza ``self._listener``; el listener de fondo ya está pausado,
        por lo que jamás se abren dos capturas de micrófono simultáneas.
        """
        audio = self._speaker.synthesize(text)
        capture_stop = threading.Event()
        interruption = threading.Event()
        result = {"text": ""}

        def capture():
            try:
                candidate = self._listener.listen(capture_stop)
                if candidate and self.is_wake_word(candidate):
                    result["text"] = candidate
                    interruption.set()
            except Exception as error:
                print(f"[Voice] Wake interruption unavailable: {error}")

        worker = threading.Thread(target=capture, name="ambar-barge-in", daemon=False)
        worker.start()
        try:
            self._speaker.play_interruptible(audio, interruption)
        finally:
            capture_stop.set()
            worker.join(timeout=2)
        return result["text"] or None

    # ===========================
    # Wake Word
    # ===========================

    def is_wake_word(self, text):

        return self._wakeword.detect(text)
