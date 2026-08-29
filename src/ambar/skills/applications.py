import subprocess

from ambar.skills.base import Skill


class ApplicationSkill(Skill):

    def __init__(self):

        self.apps = {
            "bloc": "notepad.exe",
            "bloc de notas": "notepad.exe",
            "notepad": "notepad.exe",

            "calculadora": "calc.exe",
            "calc": "calc.exe",

            "paint": "mspaint.exe",

            "cmd": "cmd.exe",

            "explorador": "explorer.exe",

            "vscode": "code",
            "visual studio code": "code",

            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",

            "spotify": "spotify.exe",
        }

    def can_execute(self, message: str):

        return message.lower().startswith("abre ")

    def execute(self, message: str):

        app = message.lower().replace("abre ", "", 1).strip()

        if app not in self.apps:
            return None

        try:
            subprocess.Popen(self.apps[app])
        except OSError as error:
            return f"No pude abrir {app}: {error}."

        return f"Abriendo {app}."
