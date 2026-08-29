import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

import ambar.voice.microphone as microphone_module


class _FakeVAD:
    def __init__(self):
        self.calls = 0

    def detect(self, _audio, _sample_rate):
        self.calls += 1
        return 1 <= self.calls <= 3


class _SilentVAD:
    def detect(self, _audio, _sample_rate):
        return False


class _WindowAwareVAD:
    def __init__(self):
        self.lengths = []

    def detect(self, audio, _sample_rate):
        self.lengths.append(len(audio))
        return False


class _FakeStream:
    def __init__(self, blocks):
        self._blocks = iter(blocks)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, frames):
        data = next(self._blocks)
        assert len(data) == frames
        return data, False


class MicrophoneTests(unittest.TestCase):
    def test_records_speech_and_keeps_debug_copy(self):
        calibration = np.full((24000, 1), 0.002, dtype=np.float32)
        speech = [np.full((1600, 1), 0.04, dtype=np.float32) for _ in range(3)]
        silence = [np.zeros((1600, 1), dtype=np.float32) for _ in range(16)]
        streams = iter([_FakeStream([calibration]), _FakeStream(speech + silence)])

        with patch.object(microphone_module, "VoiceActivityDetector", _FakeVAD), patch.object(
            microphone_module.sd, "InputStream", side_effect=lambda **_kwargs: next(streams)
        ):
            microphone = microphone_module.Microphone()
            with tempfile.TemporaryDirectory() as directory:
                microphone._debug_audio = Path(directory) / "debug.wav"
                audio = microphone.record()
                self.assertTrue(Path(audio).exists())
                self.assertTrue(microphone._debug_audio.exists())
                self.assertGreater(microphone._debug_audio.stat().st_size, 44)
                os.unlink(audio)

    def test_vad_receives_a_rolling_audio_window(self):
        calibration = np.full((24000, 1), 0.002, dtype=np.float32)
        blocks = [np.full((1600, 1), 0.04, dtype=np.float32) for _ in range(2)]
        blocks += [np.zeros((1600, 1), dtype=np.float32) for _ in range(16)]
        streams = iter([_FakeStream([calibration]), _FakeStream(blocks)])
        vad = _WindowAwareVAD()

        with patch.object(microphone_module, "VoiceActivityDetector", return_value=vad), patch.object(
            microphone_module.sd, "InputStream", side_effect=lambda **_kwargs: next(streams)
        ):
            microphone = microphone_module.Microphone()
            with tempfile.TemporaryDirectory() as directory:
                microphone._debug_audio = Path(directory) / "debug.wav"
                audio = microphone.record()
                self.assertTrue(Path(audio).exists())
                self.assertIn(8000, vad.lengths)
                os.unlink(audio)

    def test_uses_rms_when_vad_misses_short_speech_blocks(self):
        calibration = np.full((24000, 1), 0.002, dtype=np.float32)
        speech = [np.full((1600, 1), 0.04, dtype=np.float32) for _ in range(2)]
        silence = [np.zeros((1600, 1), dtype=np.float32) for _ in range(16)]
        streams = iter([_FakeStream([calibration]), _FakeStream(speech + silence)])

        with patch.object(microphone_module, "VoiceActivityDetector", _SilentVAD), patch.object(
            microphone_module.sd, "InputStream", side_effect=lambda **_kwargs: next(streams)
        ):
            microphone = microphone_module.Microphone()
            with tempfile.TemporaryDirectory() as directory:
                microphone._debug_audio = Path(directory) / "debug.wav"
                audio = microphone.record()
                self.assertTrue(Path(audio).exists())
                os.unlink(audio)
