import json
import re
import subprocess
from pathlib import Path

from ambar.actions.system_apps import SystemApplicationFinder
from ambar.core.paths import writable_config_root
from ambar.skills.base import Skill


class ApplicationSkill(Skill):
    """Abre aplicaciones conocidas y aprende comandos seguros por conversación."""

    _DANGEROUS = re.compile(
        r"[&|;<>`]|\b(?:powershell|cmd(?:\.exe)?|del|erase|format|shutdown|reg(?:\.exe)?)\b",
        re.I,
    )

    # Variantes que Whisper suele transcribir mal
    _VOICE_CHOICES = (
        "voz", "por voz", "la voz", "con voz",
        "bos", "vos", "bus", "box", "boz", "bóz",
        "con palabras", "palabras", "te lo digo", "te lo enseño",
        "dictar", "dictado", "hablando", "por hablar",
    )
    _MANUAL_CHOICES = (
        "manual", "manualmente", "escribir", "escribirlo", "escribiendolo",
        "escribiendo", "ruta", "la ruta", "texto", "con texto",
        "teclado", "cuadro", "ventana", "digitar", "tipear",
    )

    def __init__(self, events=None):
        self._events = events
        self.apps = {
            "bloc": "notepad.exe",
            "bloc de notas": "notepad.exe",
            "notepad": "notepad.exe",
            "calculadora": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",
            "explorador": "explorer.exe",
            "explorador de archivos": "explorer.exe",
            "vscode": "code",
            "visual studio code": "code",
            "vs code": "code",
            "brave": "brave.exe",
            "navegador": "brave.exe",
            "navegador brave": "brave.exe",
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "spotify": "spotify.exe",
        }
        self._file = writable_config_root() / "learned_apps.json"
        self._learned = self._load()
        self._pending_app = None
        self._candidate = None
        self._awaiting_command = False

    def can_execute(self, message):
        return self._pending_app is not None or message.casefold().strip().startswith("abre ")

    def execute(self, message):
        text = message.strip()
        low = message.casefold().strip()

        if self._pending_app:
            return self._continue_learning(text, low)

        app = low.removeprefix("abre ").strip(" .")
        if not app:
            return "¿Qué aplicación quieres que abra?"

        if app in self.apps:
            return self._launch(app, self.apps[app])

        if app in self._learned:
            return self._launch(app, self._learned[app]["command"])

        # Alias dentro de learned
        for key, data in self._learned.items():
            aliases = data.get("aliases", [])
            if app == key or app in aliases:
                return self._launch(app, data["command"])

        candidate = SystemApplicationFinder().find(app)
        if candidate:
            self._pending_app = app
            self._candidate = candidate
            return f"Creo que es {candidate['name']}. ¿Lo abro? Sí o no."

        self._pending_app = app
        return (
            f"No sé abrir {app} todavía. "
            "¿Me lo enseñas por voz o prefieres escribir la ruta manualmente?"
        )

    def handle_gui_result(self, data):
        """Recibe el resultado del diálogo ejecutado por el hilo de Qt."""
        if not self._pending_app:
            return
        if not data or data.get("app") != self._pending_app:
            return
        if data.get("cancelled"):
            self._clear_pending()
            response = "Entendido, cancelé el aprendizaje."
        else:
            response = self._save_learned(self._pending_app, data.get("command", ""))
        if self._events is not None:
            self._events.emit("teach_app.response", response)
    def _continue_learning(self, text, low):
        app = self._pending_app

        if self._candidate:
            if low in {"si", "sí", "si abrelo", "sí ábrelo", "abrelo", "ábrelo"}:
                candidate = self._candidate
                self._candidate = None
                self._learned[app] = {"command": candidate["command"], "aliases": [app]}
                self._file.parent.mkdir(parents=True, exist_ok=True)
                self._file.write_text(json.dumps(self._learned, ensure_ascii=False, indent=2), encoding="utf-8")
                self._clear_pending()
                return self._launch(app, candidate["command"])
            if low in {"no", "no gracias", "cancelar", "cancela"}:
                self._candidate = None
                return "Entendido. ¿Me lo enseñas por voz o prefieres escribir la ruta manualmente?"
            return "Responde sí para abrirlo o no para enseñarme la aplicación."

        # Cancelar
        if any(w in low for w in ("cancelar", "cancela", "no", "olvidalo", "olvídalo")):
            self._clear_pending()
            return "Entendido, cancelé el aprendizaje."

        if not self._awaiting_command:
            if self._matches_any(low, self._VOICE_CHOICES):
                self._awaiting_command = True
                return "Adelante, dime cómo es la ruta o el comando."

            if self._matches_any(low, self._MANUAL_CHOICES):
                if self._events is None:
                    return "No puedo abrir el cuadro manual en este momento."
                self._events.emit("gui.teach_app.request", {"app": app})
                return "Abriendo el cuadro para escribir la ruta."

            return "Indica 'voz' o 'manual'."

        # Ya está esperando la ruta/comando
        return self._save_learned(app, text)

    @staticmethod
    def _matches_any(text, choices):
        return any(choice in text for choice in choices)

    def _save_learned(self, app, command):
        command = command.strip().strip('"').strip("'")
        if not self._is_safe(command):
            return (
                "Esa ruta o comando no es seguro. "
                "Dime una ruta de aplicación o un ejecutable válido."
            )

        self._learned[app] = {"command": command, "aliases": [app]}
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(
            json.dumps(self._learned, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._clear_pending()
        return f"Listo. Ya aprendí a abrir {app}."

    def _clear_pending(self):
        self._pending_app = None
        self._candidate = None
        self._awaiting_command = False

    def _launch(self, app, command):
        try:
            # Si es ruta con espacios, conviene lista
            if Path(command).is_file():
                subprocess.Popen(command)
            else:
                subprocess.Popen(command)
        except OSError as error:
            return f"No pude abrir {app}: {error}."
        return f"Abriendo {app}."

    def _load(self):
        try:
            if self._file.exists():
                return json.loads(self._file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def _is_safe(self, command):
        if not command:
            return False
        if self._DANGEROUS.search(command):
            return False
        if command.lower().endswith(".exe"):
            return True
        if Path(command).is_file():
            return True
        # nombre simple tipo discord.exe / code
        return re.fullmatch(r"[\w.-]+", command) is not None

