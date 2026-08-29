from pathlib import Path

import numpy as np
from scipy.io.wavfile import read

from ambar.voice.microphone import Microphone
from ambar.voice.engines.whisper_engine import WhisperEngine


class Listener:
    """
    Captura audio y lo convierte en texto.

    Mantiene una única instancia del micrófono
    y una única instancia de Whisper.
    """

    def __init__(self):

        self.microphone = Microphone()

        self.engine = WhisperEngine()

        # Longitud mínima aceptada
        self._min_text_length = 2

    # =========================================

    def listen(self, stop_event=None):

        audio = self.microphone.record(stop_event)

        return self._process(audio)

    # =========================================

    def listen_until(self, stop_event):

        audio = self.microphone.record_until(stop_event)

        return self._process(audio)

    # =========================================

    def _process(self, audio):

        if audio is None:
            return ""

        audio_path = Path(audio)
        sample_rate, samples = read(audio_path)
        normalized = samples.astype(np.float32)
        if np.issubdtype(samples.dtype, np.integer):
            normalized /= np.iinfo(samples.dtype).max
        rms = float(np.sqrt(np.mean(np.square(normalized))))
        peak = float(np.max(np.abs(normalized)))
        duration = len(samples) / sample_rate
        print(
            f"[Listener][debug] Enviando WAV a Whisper: {audio_path} | "
            f"duración: {duration:.2f}s | frecuencia: {sample_rate}Hz | "
            f"RMS: {rms:.4f} | pico: {peak:.4f} | "
            f"tamaño: {audio_path.stat().st_size} bytes"
        )

        try:

            text = self.engine.transcribe(audio)

        finally:

            audio_path.unlink(missing_ok=True)

        if text is None:
            return ""

        text = text.strip()

        if len(text) < self._min_text_length:
            return ""

        return text
