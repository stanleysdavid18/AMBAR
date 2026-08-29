from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Interfaz base para cualquier proveedor de IA.
    """

    @abstractmethod
    def generate(self, message: str) -> str:
        """
        Genera una respuesta.
        """
        pass