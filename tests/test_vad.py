import unittest
from types import SimpleNamespace

from ambar.voice.engines.whisper_engine import WhisperEngine


class _Model:
    def transcribe(self, _filename, **_kwargs):
        return iter([
            SimpleNamespace(start=0.0, end=0.5, text=" Hola Ámbar ", no_speech_prob=0.9)
        ]), SimpleNamespace(language="es", language_probability=0.99)


class WhisperEngineTests(unittest.TestCase):
    def test_keeps_text_when_probability_filter_discards_every_segment(self):
        engine = WhisperEngine.__new__(WhisperEngine)
        engine.model = _Model()
        self.assertEqual(engine.transcribe("debug.wav"), "Hola Ámbar")
