from datetime import datetime
from ambar.brain.intent import Intent


class RuleEngine:

    def detect(self, message: str) -> Intent:

        text = message.lower().strip()

        if text == "hora":
            return Intent.GET_TIME

        if text == "fecha":
            return Intent.GET_DATE

        if text == "memoria":
            return Intent.SHOW_MEMORY

        if text == "datos":
            return Intent.SHOW_FACTS

        return Intent.CHAT

    def execute(self, intent: Intent):

        if intent == Intent.GET_TIME:
            return datetime.now().strftime("Son las %H:%M")

        if intent == Intent.GET_DATE:
            return datetime.now().strftime("Hoy es %d/%m/%Y")

        return None