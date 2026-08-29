import json
import re
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QInputDialog
from ambar.core.paths import application_root
from ambar.skills.base import Skill

class ApplicationSkill(Skill):
    """Abre aplicaciones conocidas y aprende comandos seguros por conversación."""
    _DANGEROUS = re.compile(r"[&|;<>`]|\b(?:powershell|cmd(?:\.exe)?|del|erase|format|shutdown|reg(?:\.exe)?)\b", re.I)
    def __init__(self):
        self.apps = {"bloc":"notepad.exe", "bloc de notas":"notepad.exe", "notepad":"notepad.exe", "calculadora":"calc.exe", "calc":"calc.exe", "paint":"mspaint.exe", "explorador":"explorer.exe", "explorador de archivos":"explorer.exe", "vscode":"code", "visual studio code":"code", "vs code":"code", "brave":"brave.exe", "navegador":"brave.exe", "chrome":"chrome.exe", "google chrome":"chrome.exe", "spotify":"spotify.exe"}
        self._file = application_root() / "config" / "learned_apps.json"
        self._learned = self._load(); self._pending_app = None; self._awaiting_command = False
    def can_execute(self, message): return self._pending_app is not None or message.casefold().strip().startswith("abre ")
    def execute(self, message):
        text, low = message.strip(), message.casefold().strip()
        if self._pending_app: return self._continue_learning(text, low)
        app = low.removeprefix("abre ").strip(" .")
        if app in self.apps: return self._launch(app, self.apps[app])
        if app in self._learned: return self._launch(app, self._learned[app]["command"])
        self._pending_app = app
        return f"No sé abrir {app} todavía. ¿Me lo enseñas por voz o prefieres escribir la ruta manualmente?"
    def _continue_learning(self, text, low):
        app = self._pending_app
        if not self._awaiting_command:
            if any(choice in low for choice in ("voz", "por voz")):
                self._awaiting_command = True
                return "Adelante, dime cómo es la ruta o el comando."
            if any(choice in low for choice in ("manual", "escribir", "ruta")):
                command, accepted = QInputDialog.getText(None, "Enseñar aplicación", f"Ruta o comando para {app}:")
                if not accepted: self._clear_pending(); return "Entendido, cancelé el aprendizaje de la aplicación."
                return self._save_learned(app, command)
            return "Indica 'voz' o 'manual'."
        return self._save_learned(app, text)
    def _save_learned(self, app, command):
        command = command.strip().strip('"')
        if not self._is_safe(command): return "Esa ruta o comando no es seguro. Dime una ruta de aplicación o un ejecutable válido."
        self._learned[app] = {"command": command, "aliases": [app]}; self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(self._learned, ensure_ascii=False, indent=2), encoding="utf-8"); self._clear_pending()
        return f"Listo. Ya aprendí a abrir {app}."
    def _clear_pending(self): self._pending_app = None; self._awaiting_command = False
    def _launch(self, app, command):
        try: subprocess.Popen(command)
        except OSError as error: return f"No pude abrir {app}: {error}."
        return f"Abriendo {app}."
    def _load(self):
        try: return json.loads(self._file.read_text(encoding="utf-8")) if self._file.exists() else {}
        except (OSError, json.JSONDecodeError): return {}
    def _is_safe(self, command): return bool(command) and not self._DANGEROUS.search(command) and (command.lower().endswith(".exe") or Path(command).is_file() or re.fullmatch(r"[\w.-]+", command) is not None)
