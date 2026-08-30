from ambar.config.manager import ConfigManager
from ambar.core.state import SystemState
from ambar.voice.background_listener import BackgroundListener
from ambar.voice.listener import Listener
from ambar.voice.speaker import Speaker
from ambar.wakeword import WakeWordDetector
import threading


class VoiceService:
    """Única puerta para escucha, TTS y wake word."""

    def __init__(self, listener=None, speaker=None, wakeword=None, events=None, states=None):
        self._listener = listener
        self._speaker = speaker
        self._wakeword = wakeword or WakeWordDetector()
        self._background_listener = None
        self._listening = False
        self._speaking = False
        try:
            voice_config = ConfigManager().get("voice")
        except (FileNotFoundError, KeyError, OSError, ValueError):
            voice_config = {}
        self._barge_in_enabled = bool(voice_config.get("barge_in_enabled", True))
        self._microphone_enabled = True
        self._events = events
        self._states = states
        self._lock = threading.RLock()
        if self._events:
            self._events.subscribe("gui.microphone.set", self._set_microphone)
            self._events.subscribe("voice.settings.changed", self._apply_voice_settings)

    def _apply_voice_settings(self, settings):
        self._barge_in_enabled = bool(settings.get("barge_in_enabled", self._barge_in_enabled))
        microphone = getattr(self._listener, "microphone", None)
        if microphone is not None:
            microphone.apply_voice_settings(settings)

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

    def start(self):
        with self._lock:
            if not self._microphone_enabled:
                return False
            if self._listening and self._background_listener and self._background_listener.running:
                return True
            self._listener = self._listener or Listener()
            self._background_listener = self._background_listener or BackgroundListener(self._listener)
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

    @property
    def speaking(self):
        return self._speaking

    def next_message(self, timeout=None):
        if not self._background_listener:
            return None
        return self._background_listener.get_message(timeout)

    def listen_until(self, stop_event):
        self._listener = self._listener or Listener()
        return self._listener.listen_until(stop_event)

    def speak(self, text):
        """Habla sin detener el listener de fondo.

        Mientras Piper suena, solo una frase que contenga la wake word puede
        interrumpir. Las demás transcripciones se descartan para no ejecutar
        la propia voz de Ámbar como comando.
        """
        with self._lock:
            if self._speaking:
                raise RuntimeError("Ya hay una respuesta de voz en curso.")
            self._speaking = True
        try:
            self._speaker = self._speaker or Speaker()
            if self._barge_in_enabled and self._listening and hasattr(self._speaker, "synthesize"):
                return self._speak_with_wake_filter(text)
            self._speaker.speak(text)
            return None
        finally:
            self._speaking = False
            # Nunca dejar la escucha normal detenida al finalizar TTS. Si el
            # usuario apagó el micrófono explícitamente, no la reactivamos.
            if self._microphone_enabled and not self._listening:
                self.start()

    def _speak_with_wake_filter(self, text):
        audio = self._speaker.synthesize(text)
        interrupted = threading.Event()
        result = {"text": None}
        monitoring = threading.Event()
        monitoring.set()

        def watch_listener():
            while monitoring.is_set() and not interrupted.is_set():
                candidate = self.next_message(timeout=0.1)
                if candidate and self.is_wake_word(candidate):
                    print(f"[Voice] Interrupción detectada: {candidate!r}")
                    result["text"] = candidate
                    interrupted.set()
                    return

        worker = threading.Thread(target=watch_listener, name="ambar-barge-in", daemon=True)
        worker.start()
        try:
            self._speaker.play_interruptible(audio, interrupted)
        finally:
            monitoring.clear()
            worker.join(timeout=0.5)
        return result["text"]

    def is_wake_word(self, text):
        return self._wakeword.detect(text)

