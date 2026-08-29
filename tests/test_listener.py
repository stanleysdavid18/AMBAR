import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.io.wavfile import write

from ambar.voice.listener import Listener


class _Engine:
    def __init__(self):
        self.received = None

    def transcribe(self, filename):
        self.received = filename
        return "Hola Ámbar"


class ListenerTests(unittest.TestCase):
    def test_processes_and_removes_temporary_wav(self):
        listener = Listener.__new__(Listener)
        listener.engine = _Engine()
        listener._min_text_length = 2
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as file:
            path = Path(file.name)
        write(path, 16000, np.full(1600, 1000, dtype=np.int16))

        self.assertEqual(listener._process(str(path)), "Hola Ámbar")
        self.assertEqual(listener.engine.received, str(path))
        self.assertFalse(path.exists())
