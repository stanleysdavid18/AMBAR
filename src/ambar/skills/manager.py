from ambar.skills.registry import load_skills


class SkillManager:
    def __init__(self, events=None, ai_manager=None):
        self.skills = load_skills(events, ai_manager)

    def handle_gui_result(self, data):
        for skill in self.skills:
            handler = getattr(skill, "handle_gui_result", None)
            if handler:
                handler(data)

    def execute(self, message: str):
        for skill in self.skills:
            if skill.can_execute(message):
                return skill.execute(message)
        return None
