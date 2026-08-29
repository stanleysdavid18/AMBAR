from ambar.actions.open_programs import OpenProgramController
from ambar.skills.base import Skill


class CloseProgramsSkill(Skill):
    """Lista ventanas visibles y cierra solo la selección explícita del usuario."""

    def __init__(self, controller=None):
        self._controller = controller or OpenProgramController()
        self._programs = None

    def can_execute(self, message):
        low = message.casefold()
        return self._programs is not None or any(phrase in low for phrase in (
            "cierra programas", "cerrar programas", "cierra los programas", "qué programas cierro",
        ))

    def execute(self, message):
        if self._programs is None:
            self._programs = self._controller.list_open_programs()
            if not self._programs:
                return "No veo programas con ventana abierta para cerrar."
            listing = "; ".join(f"{index}. {program['title']}" for index, program in enumerate(self._programs, 1))
            return f"Tengo {len(self._programs)} programas abiertos: {listing}. ¿Cuál deseas que cierre?"

        choice = message.casefold().strip()
        if choice in {"cancelar", "no", "ninguno"}:
            self._programs = None
            return "Entendido, no cerraré ningún programa."

        refused = self._refusal_target(choice)
        if refused is not None:
            if refused in {"", "nada", "ninguno", "ningún programa", "ningun programa"}:
                self._programs = None
                return "Entendido, no cerraré ningún programa."

            skipped = self._controller.match(self._programs, refused)
            if skipped is None:
                return "Entendido, no cerraré ese programa. Di el nombre o número del que sí deseas cerrar."

            self._programs = [program for program in self._programs if program is not skipped]
            if not self._programs:
                return f"Entendido, no cerraré {skipped['title']}. No quedan otros programas para cerrar."
            listing = "; ".join(
                f"{index}. {program['title']}" for index, program in enumerate(self._programs, 1)
            )
            return f"Entendido, no cerraré {skipped['title']}. Puedes elegir: {listing}. ¿Cuál deseas cerrar?"

        selected = self._controller.match(self._programs, choice)
        if selected is None:
            return "No identifiqué ese programa. Di su nombre o el número de la lista."
        self._programs = None
        if self._controller.close(selected):
            return f"Cerrando {selected['title']}."
        return f"No pude solicitar el cierre de {selected['title']}."

    @staticmethod
    def _refusal_target(choice):
        for prefix in ("no quiero cerrar ", "no cierres ", "no cerrar "):
            if choice.startswith(prefix):
                return choice[len(prefix):].strip(" .")
        return None
