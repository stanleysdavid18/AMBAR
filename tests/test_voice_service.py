import unittest
from unittest.mock import patch

from ambar.services.voice_service import VoiceService


class _Listener: pass

class _Speaker:
    def __init__(self): self.messages = []
    def speak(self, text): self.messages.append(text)

class _InterruptibleSpeaker(_Speaker):
    def synthesize(self, text): self.messages.append(text); return "audio.wav"
    def play_interruptible(self, _audio, interrupted): return not interrupted.wait(timeout=0.2)

class _Background:
    instances = []
    def __init__(self, listener): self.listener, self.running, self.started, self.message = listener, False, 0, None; _Background.instances.append(self)
    def start(self): self.running = True; self.started += 1; return True
    def stop(self): self.running = False; return True
    def get_message(self, timeout=None): return self.message

class VoiceServiceTests(unittest.TestCase):
    def setUp(self): _Background.instances.clear()

    @patch("ambar.services.voice_service.BackgroundListener", _Background)
    def test_speaking_keeps_background_listener_running(self):
        speaker = _Speaker(); service = VoiceService(listener=_Listener(), speaker=speaker); service.start()
        service.speak("respuesta")
        self.assertEqual(speaker.messages, ["respuesta"])
        self.assertTrue(service.listening)
        self.assertTrue(_Background.instances[0].running)

    @patch("ambar.services.voice_service.BackgroundListener", _Background)
    def test_tts_reactivates_listener_if_a_previous_flow_paused_it(self):
        speaker = _Speaker(); service = VoiceService(listener=_Listener(), speaker=speaker)
        service.start()
        service.pause_listening()
        service.speak("respuesta")
        self.assertTrue(service.listening)
        self.assertTrue(_Background.instances[0].running)
    @patch("ambar.services.voice_service.BackgroundListener", _Background)
    def test_wake_word_interrupts_but_other_transcripts_do_not(self):
        service = VoiceService(listener=_Listener(), speaker=_InterruptibleSpeaker()); service.start()
        _Background.instances[0].message = "ruido de fondo"
        self.assertIsNone(service.speak("respuesta larga"))
        _Background.instances[0].message = "Ambar, abre calculadora"
        self.assertEqual(service.speak("respuesta larga"), "Ambar, abre calculadora")
        self.assertTrue(service.listening)
