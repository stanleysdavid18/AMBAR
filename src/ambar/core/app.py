import threading

from ambar.core.engine import Engine
from ambar.core.event_bus import EventBus
from ambar.core.state import SystemState
from ambar.core.state_manager import StateManager
from ambar.gui.app import AmberGUI


class Amber:
    def __init__(self):
        self.events = EventBus()
        self.states = StateManager(self.events)
        self.engine = Engine(self.events, self.states)
        self.gui = AmberGUI(self.events)

    def run(self):
        self.states.set(SystemState.STARTING)
        worker = threading.Thread(target=self.engine.run, daemon=True)
        worker.start()
        try:
            self.gui.run()
        finally:
            self.gui.shutdown()
            self.engine.stop()
            worker.join(timeout=3)
