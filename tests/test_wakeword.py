import unittest

from ambar.wakeword.detector import WakeWordDetector


class WakeWordTests(unittest.TestCase):
    def setUp(self):
        self.detector = WakeWordDetector()

    def test_detects_supported_forms(self):
        for text in ("Ámbar", "Hola Ámbar", "hola ambar", "¡AMBAR!"):
            with self.subTest(text=text):
                self.assertTrue(self.detector.detect(text))

    def test_does_not_match_a_partial_word(self):
        self.assertFalse(self.detector.detect("ambarino"))

    def test_ignores_mispronunciations_and_unrelated_words(self):
        for text in ("Lambar", "Lamber", "ambarino", "hola asistente"):
            with self.subTest(text=text):
                self.assertFalse(self.detector.detect(text))
