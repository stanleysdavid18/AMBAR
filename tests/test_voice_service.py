import unittest
from unittest.mock import patch

from ambar.services.voice_service import VoiceService


class _Listener:
    pass


class _Speaker:
    def __init__(self):
        self.messages = []

    def speak(self, text):
        self.messages.append(text)


class _WakeListener:
    def __init__(self, text):
        self.text = text

    def listen(self, _stop_event):
        return self.text


class _InterruptibleSpeaker(_Speaker):
    def synthesize(self, text):
        self.messages.append(text)
        return "audio.wav"

    def play_interruptible(self, _audio, interrupted):
        return not interrupted.wait(timeout=1)


class _Background:
    instances = []

    def __init__(self, listener):
        self.listener = listener
        self.running = False
        self.started = 0
        _Background.instances.append(self)

    def start(self):
        self.running = True
        self.started += 1
        return True

    def stop(self):
        self.running = False
        return True

    def get_message(self, timeout=None):
        return None


class VoiceServiceTests(unittest.TestCase):
    def setUp(self):
        _Background.instances.clear()

    @patch("ambar.services.voice_service.BackgroundListener", _Background)
    def test_pause_resume_reuses_one_listener_and_controller(self):
        listener = _Listener()
        service = VoiceService(listener=listener, speaker=_Speaker())

        self.assertTrue(service.start())
        self.assertTrue(service.pause_listening())
        self.assertTrue(service.resume_listening())

        self.assertEqual(len(_Background.instances), 1)
        self.assertIs(_Background.instances[0].listener, listener)
        self.assertEqual(_Background.instances[0].started, 2)

    @patch("ambar.services.voice_service.BackgroundListener", _Background)
    def test_speaking_pauses_and_restores_microphone(self):
        speaker = _Speaker()
        service = VoiceService(listener=_Listener(), speaker=speaker)
        service.start()

        service.speak("respuesta")

        self.assertEqual(speaker.messages, ["respuesta"])
        self.assertTrue(service.listening)
        self.assertEqual(len(_Background.instances), 1)

    def test_default_does_not_capture_microphone_while_speaking(self):
        service = VoiceService(listener=_WakeListener("Ambar, espera"), speaker=_InterruptibleSpeaker())
        self.assertIsNone(service.speak("respuesta larga"))

    def test_only_wake_word_interrupts_speech(self):
        speaker = _InterruptibleSpeaker()
        service = VoiceService(
            listener=_WakeListener("Ambar, espera"), speaker=speaker
        )
        service._barge_in_enabled = True
        self.assertEqual(service.speak("respuesta larga"), "Ambar, espera")

        service = VoiceService(
            listener=_WakeListener("espera un momento"), speaker=_InterruptibleSpeaker()
        )
        self.assertIsNone(service.speak("respuesta larga"))
