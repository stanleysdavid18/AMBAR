from ambar.modes.normal import NormalMode
from ambar.modes.study import StudyMode
from ambar.modes.work import WorkMode
from ambar.modes.gaming import GamingMode


class ModeManager:

    def __init__(self):

        self.modes = {
            "normal": NormalMode(),
            "study": StudyMode(),
            "work": WorkMode(),
            "gaming": GamingMode(),
        }

        self.current = self.modes["normal"]

    def get(self):

        return self.current

    def set(self, name):

        if name not in self.modes:
            return None

        self.current.on_exit()

        self.current = self.modes[name]

        self.current.on_enter()

        return self.current

    def current_name(self):

        return self.current.name
