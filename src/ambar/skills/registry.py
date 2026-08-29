from ambar.skills.applications import ApplicationSkill
from ambar.skills.close_programs import CloseProgramsSkill
from ambar.skills.desktop_folder import DesktopFolderSkill
from ambar.skills.browser import BrowserSkill
from ambar.skills.system import SystemSkill


def load_skills(events=None, ai_manager=None):
    return [
        CloseProgramsSkill(),
        BrowserSkill(ai_manager),
        DesktopFolderSkill(),
        ApplicationSkill(events),
        SystemSkill(),
    ]
