import unittest
from unittest.mock import patch

from ambar.memory.working_memory import WorkingMemory
from ambar.skills.applications import ApplicationSkill


class ApplicationsAndMemoryTests(unittest.TestCase):
    def test_memory_keeps_a_bounded_recent_context(self):
        memory = WorkingMemory(max_messages=3)
        for index in range(5):
            memory.add("user", str(index))
        self.assertEqual([item["content"] for item in memory.history()], ["2", "3", "4"])

    @patch("ambar.skills.applications.subprocess.Popen")
    def test_opens_known_desktop_apps_without_ai(self, popen):
        skill = ApplicationSkill()
        self.assertEqual(skill.execute("abre calculadora"), "Abriendo calculadora.")
        popen.assert_called_once_with("calc.exe")
