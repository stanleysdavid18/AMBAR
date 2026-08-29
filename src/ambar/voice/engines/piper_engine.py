import subprocess

from ambar.config.manager import ConfigManager
from ambar.core.paths import application_root, writable_runtime
from ambar.voice.engines.base_engine import BaseTTSEngine


class PiperEngine(BaseTTSEngine):
    """
    Motor de voz utilizando Piper.
    """

    def __init__(self):

        self.config = ConfigManager()

        root = application_root()

        self.piper = root / "runtime" / "piper" / "piper.exe"

        voice = self.config.get("voice", "model")

        self.voice = root / "models" / "voices" / voice

        self.output = writable_runtime() / "audio"

        self.output.mkdir(parents=True, exist_ok=True)

        self.output_file = self.output / "speech.wav"

    def speak(self, text: str):

        print("[Piper] Generando voz...")

        subprocess.run(
            [
                str(self.piper),
                "--model",
                str(self.voice),
                "--output_file",
                str(self.output_file)
            ],
            input=text,
            text=True,
            check=True
        )
        if not self.output_file.exists():
            raise RuntimeError("Piper no generó el archivo de audio.")
        if self.output_file.stat().st_size == 0:
            raise RuntimeError("El archivo de audio está vacío.")

        print("[Piper] Voz generada.")

        return self.output_file
