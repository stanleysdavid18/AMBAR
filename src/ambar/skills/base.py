from abc import ABC, abstractmethod


class Skill(ABC):
    """
    Clase base para todas las Skills de Ámbar.
    """

    @abstractmethod
    def can_execute(self, message: str) -> bool:
        pass

    @abstractmethod
    def execute(self, message: str):
        pass