from silero_vad import load_silero_vad, get_speech_timestamps
import torch


class VoiceActivityDetector:
    """
    Detector de actividad de voz utilizando Silero VAD.
    """

    def __init__(self):

        print("[VAD] Cargando Silero...")

        self.model = load_silero_vad()

        print("[VAD] Listo.")

    def detect(self, audio, sample_rate=16000):

        if not isinstance(audio, torch.Tensor):
            audio = torch.tensor(audio, dtype=torch.float32)

        timestamps = get_speech_timestamps(
            audio,
            self.model,
            sampling_rate=sample_rate
        )

        return timestamps