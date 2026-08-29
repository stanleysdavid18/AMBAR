import re
import unicodedata


class WakeWordDetector:
    """Detecta la palabra de activación con o sin tilde y puntuación."""

    WAKE_WORD = "ambar"

    def detect(self, text: str) -> bool:
        normalized = unicodedata.normalize("NFD", text.casefold())
        normalized = "".join(
            character for character in normalized if not unicodedata.combining(character)
        )
        words = re.findall(r"\w+", normalized)
        return self.WAKE_WORD in words
