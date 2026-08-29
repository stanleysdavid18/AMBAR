"""Control explícito de interfaz Windows para habilidades de AMBAR."""
from pathlib import Path
from urllib.parse import quote_plus
import subprocess
import time

class DesktopController:
    def _ui(self):
        import pyautogui
        pyautogui.PAUSE = 0.15
        return pyautogui

    def capture_screen(self, path):
        image = self._ui().screenshot()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination)
        return destination

    def click(self, x, y): self._ui().click(x, y)
    def type_text(self, text): self._ui().write(text, interval=0.02)
    def hotkey(self, *keys): self._ui().hotkey(*keys)

    def open_chrome(self, url=None):
        subprocess.Popen(["chrome.exe", url or "https://www.google.com"])
        time.sleep(1)

    def search_youtube(self, query):
        self.open_chrome("https://www.youtube.com/results?search_query=" + quote_plus(query))

    def open_vscode(self, path="."):
        subprocess.Popen(["code", str(path)])

    def open_file_in_vscode(self, path, line=None):
        target = str(Path(path).resolve())
        command = ["code", "--goto", f"{target}:{line or 1}"]
        subprocess.Popen(command)