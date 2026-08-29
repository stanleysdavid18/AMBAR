from ambar.skills.registry import load_skills


class SkillManager:

    def __init__(self):

        self.skills = load_skills()

    def execute(self, message: str):

        for skill in self.skills:

            if skill.can_execute(message):

                return skill.execute(message)

        return None