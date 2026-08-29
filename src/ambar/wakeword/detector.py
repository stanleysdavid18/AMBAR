import re
import unicodedata


class WakeWordDetector:
    """Detecta la palabra de activación con o sin tilde y puntuación."""

    WAKE_WORDS = {"ambar", "amvar", "ampar", "ambar"}

    def detect(self, text: str) -> bool:
        normalized = unicodedata.normalize("NFD", text.casefold())
        normalized = "".join(
            character for character in normalized if not unicodedata.combining(character)
        )
        words = re.findall(r"\w+", normalized)
        return any(word in self.WAKE_WORDS for word in words)
