from ambar.ai.manager import AIManager
from ambar.brain.rules import RuleEngine
from ambar.brain.intent import Intent
from ambar.brain.planner import Planner
from ambar.brain.response import BrainResponse
from ambar.skills import SkillManager
from ambar.context import ContextManager
from ambar.actions import OpenApplication
from ambar.modes.manager import ModeManager


class Brain:
    """
    Cerebro principal de Ámbar.
    """

    def __init__(self, events=None):

        self.context = ContextManager()
        self.planner = Planner()
        self.ai = AIManager()
        self.skills = SkillManager(events, self.ai)
        self.rules = RuleEngine()

        self.mode_manager = ModeManager()

    def think(self, message: str) -> BrainResponse:

        text = message.lower().strip()

        # ==========================
        # Cambio de modo
        # ==========================

        if "modo estudio" in text:

            mode = self.mode_manager.set("study")

            return BrainResponse(
                text=mode.greeting(),
                speak=True,
                remember=False,
                emotion="happy"
            )

        if "modo normal" in text:

            mode = self.mode_manager.set("normal")

            return BrainResponse(
                text=mode.greeting(),
                speak=True,
                remember=False,
                emotion="happy"
            )

        if "modo trabajo" in text:
            mode = self.mode_manager.set("work")
            return BrainResponse(text=mode.greeting(), speak=True, remember=False, emotion="focused")

        if "modo videojuegos" in text or "modo juego" in text:
            mode = self.mode_manager.set("gaming")
            return BrainResponse(text=mode.greeting(), speak=True, remember=False, emotion="excited")

        # ==========================
        # Abrir aplicaciones
        # ==========================

        if text == "abre bloc":

            return BrainResponse(
                text="Abriendo el Bloc de notas.",
                speak=True,
                remember=False,
                emotion="neutral",
                actions=[
                    OpenApplication("notepad")
                ]
            )

        # ==========================
        # Flujo normal
        # ==========================

        tasks = self.planner.plan(message)

        responses = []

        for task in tasks:

            # Ejecutar Skills
            skill_response = self.skills.execute(task)

            if skill_response is not None:

                responses.append(skill_response)

                continue

            # Detectar intención
            intent = self.rules.detect(task)

            if intent == Intent.CHAT:

                response = self.ai.generate(
                    task,
                    system_prompt=self.mode_manager
                        .get()
                        .system_prompt()
                )

                responses.append(response)

                continue

            rule_response = self.rules.execute(intent)

            if rule_response is not None:

                responses.append(rule_response)

        if responses:

            return BrainResponse(
                text="\n".join(responses),
                speak=True,
                remember=True,
                emotion="neutral"
            )

        return BrainResponse(
            text="Todavía no sé cómo hacer eso.",
            speak=True,
            remember=False,
            emotion="neutral"
        )

    def wake_greeting(self):
        return self.mode_manager.get().wake_greeting()

    def casual_prompt(self):
        """Una única intervención breve; el scheduler decide cuándo usarla."""
        return self.ai.generate_initiative(
            "Genera una sola intervención casual breve para el usuario. No inventes "
            "hechos, no digas que observas su entorno y no hagas más de una pregunta.",
            system_prompt=(
                self.mode_manager.get().system_prompt()
                + "\nLa respuesta debe tener una frase cálida y breve (máximo 18 palabras)."
            ),
        )

