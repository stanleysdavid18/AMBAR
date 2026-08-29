from ambar.brain import Brain
from ambar.conversation import ConversationService
from ambar.services import VoiceService


class Engine:
    """Composición e inicio del núcleo de Ámbar; no contiene lógica de hardware."""

    def __init__(self, events, states, brain=None, voice=None):
        self.voice = voice or VoiceService(events=events, states=states)
        self.brain = brain or Brain(events)
        events.subscribe("gui.teach_app.result", self.brain.skills.handle_gui_result)
        self.conversation = ConversationService(
            brain=self.brain, voice=self.voice, states=states, events=events
        )

    def run(self):
        self.conversation.start()

    def stop(self):
        self.conversation.stop()
        self.voice.stop()