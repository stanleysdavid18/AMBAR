import unittest

from ambar.modes.normal import NormalMode
from ambar.modes.study import StudyMode
from ambar.modes.work import WorkMode
from ambar.modes.gaming import GamingMode


class ModeTests(unittest.TestCase):
    def test_normal_mode_uses_venezuelan_personality(self):
        mode = NormalMode()
        self.assertIn("chamo", mode.wake_greeting().lower())
        self.assertIn("venezolano", mode.system_prompt().lower())

    def test_study_mode_uses_structured_teaching_prompt(self):
        mode = StudyMode()
        self.assertIn("paso a paso", mode.greeting().lower())
        self.assertIn("paso a paso", mode.system_prompt().lower())

    def test_work_and_gaming_modes_have_distinct_priorities(self):
        self.assertIn("productividad", WorkMode().system_prompt().lower())
        self.assertIn("videojuegos", GamingMode().system_prompt().lower())
