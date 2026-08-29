import unittest

from ambar.conversation.service import ConversationService
from ambar.core.event_bus import EventBus
from ambar.core.state import SystemState
from ambar.core.state_manager import StateManager
from ambar.conversation.casual import CasualController


class FakeVoice:
    def __init__(self):
        self.spoken = []

    def is_wake_word(self, text):
        return "ambar" in text.lower() or "ámbar" in text.lower()

    def speak(self, text):
        self.spoken.append(text)

    def pause_listening(self):
        pass

    def resume_listening(self):
        pass

    def listen_until(self, _stop_event):
        return "Hola Ámbar"


class FakeBrain:
    def __init__(self):
        self.messages = []

    def think(self, message):
        self.messages.append(message)
        return type("Response", (), {"text": "Respuesta", "speak": True, "actions": []})()

    def wake_greeting(self):
        return "Epa, chamo. Aquí estoy, ¿cómo estás?"


class ConversationServiceTests(unittest.TestCase):
    def setUp(self):
        self.events = EventBus()
        self.states = StateManager(self.events)
        self.voice = FakeVoice()
        self.brain = FakeBrain()
        self.service = ConversationService(self.brain, self.voice, self.states, self.events)
        self.service._running = True

    def test_keeps_listening_after_a_response(self):
        self.service.handle("Hola Ámbar")
        self.service.handle("¿Cómo estás?")
        self.assertEqual(self.brain.messages, ["¿Cómo estás?"])
        self.assertEqual(self.states.current, SystemState.LISTENING)

    def test_sleeps_on_command(self):
        self.service.handle("Ámbar")
        self.service.handle("duerme")
        self.assertEqual(self.states.current, SystemState.SLEEPING)

    def test_sleep_command_accepts_a_phrase_with_accents(self):
        self.service.handle("Ambar")
        self.service.handle("Vete a dormir")
        self.assertEqual(self.states.current, SystemState.SLEEPING)

    def test_idle_timer_is_configured_to_one_minute(self):
        self.service._last_activity = 0
        self.service.handle("Ambar")
        self.assertEqual(self.service._idle_timeout_seconds, 60)
        self.assertGreater(self.service._last_activity, 0)

    def test_manual_transcription_enters_conversation_flow(self):
        self.service._run_test()
        self.assertEqual(self.voice.spoken, ["Epa, chamo. Aquí estoy, ¿cómo estás?"])
        self.assertEqual(self.states.current, SystemState.LISTENING)

    def test_ai_failure_is_reported_without_raising(self):
        class FailingBrain(FakeBrain):
            def think(self, _message):
                raise ConnectionError("Ollama unavailable")

        errors = []
        self.events.subscribe("conversation.error", errors.append)
        self.service._brain = FailingBrain()
        self.service.handle("Ambar")
        self.service.handle("explicame Python")

        self.assertEqual(errors, ["No puedo conectarme con el motor de IA."])
        self.assertEqual(self.states.current, SystemState.ERROR)

    def test_casual_commands_are_an_optional_normal_mode_feature(self):
        casual = CasualController({"sleep_seconds": 30, "cooldown_seconds": 300, "jitter_seconds": 0})
        self.service._casual = casual
        self.service.handle("Ambar")
        self.service.handle("Activa modo casual")
        self.assertTrue(casual.enabled)
        self.service.handle("Desactiva modo casual")
        self.assertFalse(casual.enabled)
