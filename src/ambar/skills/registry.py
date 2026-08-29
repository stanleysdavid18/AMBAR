from ambar.skills.applications import ApplicationSkill
from ambar.skills.desktop_folder import DesktopFolderSkill
from ambar.skills.browser import BrowserSkill
from ambar.skills.system import SystemSkill


def load_skills():

    return [
        BrowserSkill(),
        DesktopFolderSkill(),
        ApplicationSkill(),
        SystemSkill()
    ]