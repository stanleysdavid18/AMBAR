from abc import ABC


class BaseMode(ABC):
    """
    Clase base para todos los modos.
    """

    name = "base"

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def system_prompt(self):
        return ""

    def greeting(self):
        return None

    def wake_greeting(self):
        return "Aquí estoy."
