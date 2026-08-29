from abc import ABC, abstractmethod


class BaseTTSEngine(ABC):
    """
    Clase base para cualquier motor de voz.
    """

    @abstractmethod
    def speak(self, text: str):
        pass