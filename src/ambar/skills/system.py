from datetime import datetime

from ambar.skills.base import Skill


class SystemSkill(Skill):

    def can_execute(self, message: str):

        text = message.lower().strip()

        return text in ["hora", "fecha"]

    def execute(self, message: str):

        text = message.lower().strip()

        if text == "hora":
            return datetime.now().strftime("Son las %H:%M")

        if text == "fecha":
            return datetime.now().strftime("Hoy es %d/%m/%Y")

        return None
