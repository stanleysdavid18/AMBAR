from abc import ABC, abstractmethod


class Action(ABC):
    """
    Clase base para cualquier acción ejecutable.
    """

    @abstractmethod
    def execute(self):
        pass