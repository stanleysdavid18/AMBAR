import unittest

from ambar.skills.close_programs import CloseProgramsSkill


class _Controller:
    def __init__(self): self.closed = None
    def list_open_programs(self):
        return [{"title": "Brave", "hwnd": 1}, {"title": "Deltarune", "hwnd": 2}]
    def match(self, programs, choice):
        if choice.isdigit() and 1 <= int(choice) <= len(programs):
            return programs[int(choice) - 1]
        return next((program for program in programs if program["title"].casefold() in choice), None)
    def close(self, program): self.closed = program; return True


class CloseProgramsSkillTests(unittest.TestCase):
    def test_lists_and_closes_numbered_selection(self):
        controller = _Controller(); skill = CloseProgramsSkill(controller)
        self.assertIn("1. Brave", skill.execute("ambar cierra programas"))
        self.assertEqual(skill.execute("2"), "Cerrando Deltarune.")
        self.assertEqual(controller.closed["title"], "Deltarune")

    def test_can_exclude_a_program_before_selecting_another(self):
        controller = _Controller(); skill = CloseProgramsSkill(controller)
        skill.execute("ambar cierra programas")
        reply = skill.execute("no quiero cerrar brave")
        self.assertIn("no cerraré Brave", reply)
        self.assertIn("1. Deltarune", reply)
        self.assertEqual(skill.execute("1"), "Cerrando Deltarune.")
