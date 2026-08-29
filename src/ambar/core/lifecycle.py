from ambar.core.engine import Engine
from ambar.core.state import SystemState


class Lifecycle:
    """
    Controla el ciclo de vida de Ámbar.
    """

    def __init__(self):
        self.state = SystemState.OFFLINE
        self.engine = Engine()

    def start(self):

        print("Inicializando sistema...")

        self.state = SystemState.STARTING

        print("Sistema listo.")

        self.state = SystemState.READY

        self.engine.run()