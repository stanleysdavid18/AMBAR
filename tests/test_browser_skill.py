import unittest
from unittest.mock import Mock

from ambar.skills.browser import BrowserSkill


class BrowserSkillTests(unittest.TestCase):
    def test_opens_valid_direct_url_from_ai(self):
        ai = Mock()
        ai.generate_initiative.return_value = "https://www.youtube.com/watch?v=abc123"
        skill = BrowserSkill(ai)
        skill.desktop = Mock()
        self.assertIn("Reproduciendo el video", skill.execute("abre YouTube y busca jazz"))
        skill.desktop.open_browser.assert_called_once_with("https://www.youtube.com/watch?v=abc123")

    def test_falls_back_to_search_and_first_video(self):
        ai = Mock()
        ai.generate_initiative.return_value = "sin URL"
        skill = BrowserSkill(ai)
        skill.desktop = Mock()
        skill.execute("abre YouTube y busca jazz, reproduce la primera")
        skill.desktop.search_youtube.assert_called_once_with("jazz")
        skill.desktop.play_first_youtube_result.assert_called_once_with(wait_seconds=5)
