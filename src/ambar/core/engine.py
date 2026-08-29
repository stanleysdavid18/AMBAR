from ambar.brain import Brain
from ambar.conversation import ConversationService
from ambar.services import VoiceService


class Engine:
    """Composición e inicio del núcleo de Ámbar; no contiene lógica conversacional."""

    def __init__(self, events, states, brain=None, voice=None):
        self.voice = voice or VoiceService(events=events, states=states)
        self.conversation = ConversationService(
            brain=brain or Brain(), voice=self.voice, states=states, events=events
        )

    def run(self):
        self.conversation.start()

    def stop(self):
        self.conversation.stop()
        self.voice.stop()
