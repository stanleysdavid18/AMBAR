from ambar.ai.provider import AIProvider
from ambar.personality.manager import PersonalityManager


class SimulatorProvider(AIProvider):
    """
    Simula una IA mientras conectamos una real.
    """

    def __init__(self):
        self.personality = PersonalityManager()

    def generate(self, message: str) -> str:

        message = message.lower().strip()

        responses = {

            "hola":
                "Ay vale 😊 Qué bueno volver a verte.",

            "quien eres":
                f"Soy {self.personality.get_name()}, tu asistente personal.",

            "quién eres":
                f"Soy {self.personality.get_name()}, tu asistente personal.",

            "como estas":
                "Todo excelente. ¿Qué vamos a hacer hoy?",

            "cómo estás":
                "Todo excelente. ¿Qué vamos a hacer hoy?",

            "personalidad":
                self.personality.get_prompt(),

        }

        return responses.get(
            message,
            "Todavía sigo aprendiendo, pero pronto podré responder mucho mejor."
        )