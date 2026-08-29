from pathlib import Path
import threading
import time
import wave
import winsound


class AudioPlayer:
    """
    Reproduce archivos WAV.
    """

    def play(self, file: str | Path):

        file = Path(file)

        if not file.exists():
            raise FileNotFoundError(f"No existe el audio: {file}")

        print(f"[Audio] Reproduciendo: {file.name}")

        winsound.PlaySound(
            str(file),
            winsound.SND_FILENAME
        )

        print("[Audio] Finalizado.")

    def play_interruptible(self, file: str | Path, interrupted: threading.Event) -> bool:
        """Reproduce asincrónicamente y corta sólo cuando se solicita."""
        file = Path(file)
        if not file.exists():
            raise FileNotFoundError(f"No existe el audio: {file}")
        with wave.open(str(file), "rb") as audio:
            duration = audio.getnframes() / audio.getframerate()
        winsound.PlaySound(str(file), winsound.SND_FILENAME | winsound.SND_ASYNC)
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            if interrupted.wait(timeout=0.05):
                winsound.PlaySound(None, winsound.SND_PURGE)
                return False
        return True
