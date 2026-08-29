from ambar.voice.audio import AudioPlayer
from ambar.voice.engines.piper_engine import PiperEngine
from ambar.voice.text import TextNormalizer


class Speaker:

    def __init__(self):

        self.engine = PiperEngine()
        self.player = AudioPlayer()
        self.normalizer = TextNormalizer()

    def speak(self, text: str):
        self.player.play(self.synthesize(text))

    def synthesize(self, text: str):
        return self.engine.speak(self.normalizer.normalize(text))

    def play_interruptible(self, audio, interrupted):
        return self.player.play_interruptible(audio, interrupted)
