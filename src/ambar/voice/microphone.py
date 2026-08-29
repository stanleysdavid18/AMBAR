import os
import shutil
import tempfile

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write

from ambar.config.manager import ConfigManager
from ambar.core.paths import writable_runtime
from ambar.voice.vad import VoiceActivityDetector


class Microphone:
    """Captura una frase con un único InputStream de SoundDevice."""

    def __init__(self):
        self.sample_rate = 16000
        self.block_duration = 0.1
        voice_settings = self._voice_settings()
        self.max_seconds = self._positive_float(voice_settings.get("record_max_seconds"), 45.0)
        self.silence_seconds = self._positive_float(voice_settings.get("silence_seconds"), 1.6)
        self.activation_blocks = 2
        self.min_threshold = 0.008
        self.noise_multiplier = 2.0
        self.max_threshold = 0.03
        self.threshold = self.min_threshold
        self._calibrated = False
        self._debug = True
        self._vad = VoiceActivityDetector()
        # Silero necesita una ventana mayor que un bloque de 100 ms para
        # decidir de manera estable si hay voz.
        self._vad_window_blocks = 5
        self._debug_audio = writable_runtime() / "audio" / "debug.wav"
        self._debug_audio.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _voice_settings():
        """Carga ajustes de voz sin impedir el inicio si el archivo falla."""
        try:
            return ConfigManager().get("voice")
        except (FileNotFoundError, KeyError, OSError, ValueError) as error:
            print(f"[Micrófono] Usando ajustes de escucha predeterminados: {error}")
            return {}

    @staticmethod
    def _positive_float(value, default):
        try:
            parsed = float(value)
            return parsed if parsed > 0 else default
        except (TypeError, ValueError):
            return default

    def calibrate(self, seconds=1.5):
        print("[Micrófono] Calibrando ruido ambiente...")
        frames = int(self.sample_rate * seconds)
        with self._open_stream() as stream:
            ambient, overflowed = stream.read(frames)
        if overflowed:
            print("[Micrófono] Advertencia: desbordamiento durante calibración.")

        noise_rms = self._rms(ambient)
        self.threshold = min(
            max(noise_rms * self.noise_multiplier, self.min_threshold),
            self.max_threshold,
        )
        self._calibrated = True
        self._debug_log(
            f"RMS ambiente: {noise_rms:.4f} | umbral calculado: {self.threshold:.4f}"
        )
        print(f"[Micrófono] Umbral: {self.threshold:.4f}")

    def record(self, stop_event=None):
        self._ensure_calibrated()
        print("[Micrófono] Esperando voz...")
        block_size = self._block_size
        silence_blocks = max(1, int(self.silence_seconds / self.block_duration))
        max_blocks = max(1, int(self.max_seconds / self.block_duration))
        audio, pending, vad_window = [], [], []
        speaking = False
        voice_blocks = 0
        silence_blocks_seen = 0

        with self._open_stream() as stream:
            while not self._stopped(stop_event):
                data, overflowed = stream.read(block_size)
                if overflowed:
                    print("[Micrófono] Advertencia: desbordamiento de entrada.")

                rms = self._rms(data)
                peak = float(np.max(np.abs(data)))
                vad_window.append(data)
                if len(vad_window) > self._vad_window_blocks:
                    vad_window.pop(0)
                vad_speech = self._is_speech(np.concatenate(vad_window), rms)
                rms_speech = rms >= self.threshold
                # Respaldo para voz suave: requiere dos bloques consecutivos
                # antes de abrir la grabacion, igual que RMS y VAD.
                peak_speech = peak >= max(self.threshold * 3, 0.025)
                speech = vad_speech or rms_speech or peak_speech
                self._debug_log(
                    f"RMS actual: {rms:.4f} | umbral: {self.threshold:.4f} | "
                    f"pico: {peak:.4f} | VAD: {vad_speech} | "
                    f"respaldo RMS: {rms_speech} | respaldo pico: {peak_speech} | "
                    f"estado: {'hablando' if speaking else 'esperando voz'}"
                )

                if speech:
                    silence_blocks_seen = 0
                    if speaking:
                        audio.append(data)
                    else:
                        pending.append(data)
                        voice_blocks += 1
                        self._debug_log(
                            f"Bloque de voz {voice_blocks}/{self.activation_blocks}"
                        )
                        if voice_blocks >= self.activation_blocks:
                            speaking = True
                            audio.extend(pending)
                            pending.clear()
                            print("[Micrófono] Voz detectada. Inicio de grabación.")
                elif speaking:
                    audio.append(data)
                    silence_blocks_seen += 1
                    if silence_blocks_seen >= silence_blocks:
                        print("[Micrófono] Fin de la frase por silencio.")
                        break
                else:
                    pending.clear()
                    voice_blocks = 0

                if speaking and len(audio) >= max_blocks:
                    print("[Micrófono] Tiempo máximo de frase alcanzado.")
                    break

        if self._stopped(stop_event) or not audio:
            return None
        return self._write_audio(np.concatenate(audio))

    def record_until(self, stop_event):
        """Captura manual usada exclusivamente por el modo desarrollador."""
        print("[Micrófono] Grabación manual iniciada.")
        audio = []
        with self._open_stream() as stream:
            while not self._stopped(stop_event):
                data, overflowed = stream.read(self._block_size)
                if overflowed:
                    print("[Micrófono] Advertencia: desbordamiento de entrada.")
                audio.append(data)
                rms = self._rms(data)
                self._debug_log(
                    f"RMS actual: {rms:.4f} | umbral: {self.threshold:.4f} | "
                    f"VAD: {self._is_speech(data, rms)} | estado: captura manual"
                )

        if not audio:
            return None
        return self._write_audio(np.concatenate(audio))

    @property
    def _block_size(self):
        return int(self.sample_rate * self.block_duration)

    def _open_stream(self):
        return sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self._block_size,
        )

    def _ensure_calibrated(self):
        if self._calibrated:
            return
        try:
            self.calibrate()
        except Exception as error:
            self.threshold = self.min_threshold
            self._calibrated = True
            print(f"[Micrófono] Error calibrando: {error}")

    def _is_speech(self, data, rms):
        try:
            return bool(self._vad.detect(data.reshape(-1), self.sample_rate))
        except Exception as error:
            print(f"[Micrófono] Error en VAD; usando RMS: {error}")
            return rms >= self.threshold

    @staticmethod
    def _rms(data):
        return float(np.sqrt(np.mean(np.square(data))))

    @staticmethod
    def _stopped(stop_event):
        return stop_event is not None and stop_event.is_set()

    def _debug_log(self, message):
        if self._debug:
            print(f"[Micrófono][debug] {message}")

    def _write_audio(self, samples):
        audio_int16 = np.clip(samples, -1, 1)
        audio_int16 = (audio_int16 * 32767).astype(np.int16)
        descriptor, filename = tempfile.mkstemp(suffix=".wav")
        os.close(descriptor)
        write(filename, self.sample_rate, audio_int16)
        shutil.copy2(filename, self._debug_audio)

        duration = len(samples) / self.sample_rate
        rms = self._rms(samples)
        peak = float(np.max(np.abs(samples)))
        self._debug_log(
            f"WAV: {self._debug_audio} | duración: {duration:.2f}s | "
            f"frecuencia: {self.sample_rate}Hz | RMS: {rms:.4f} | "
            f"pico: {peak:.4f} | tamaño: {self._debug_audio.stat().st_size} bytes"
        )
        return filename
