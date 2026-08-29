from pathlib import Path
from urllib.parse import quote_plus
import os
import shutil
import subprocess
import time


class DesktopController:
    def _ui(self):
        import pyautogui
        pyautogui.PAUSE = 0.2
        pyautogui.FAILSAFE = True
        return pyautogui

    def _browser(self):
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        local = Path(os.environ.get("LOCALAPPDATA", ""))

        candidates = [
            shutil.which("brave"),
            program_files / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            program_files_x86 / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            local / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            shutil.which("chrome"),
            program_files / "Google" / "Chrome" / "Application" / "chrome.exe",
            "chrome.exe",
        ]
        for item in candidates:
            if not item:
                continue
            if isinstance(item, Path):
                if item.is_file():
                    return str(item)
            else:
                return str(item)
        return "chrome.exe"

    def open_browser(self, url):
        subprocess.Popen([self._browser(), url])
        time.sleep(12)  # PC lenta

    def search_youtube(self, query):
        url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
        self.open_browser(url)

    def play_first_youtube_result(self, wait_seconds=5):
        """
        Intenta reproducir el primer resultado de YouTube.
        Estrategia más robusta que un solo Tab+Enter.
        """
        time.sleep(wait_seconds)
        ui = self._ui()

        try:
            # 1) Click aproximado en la zona del primer video (pantalla típica)
            screen_w, screen_h = ui.size()
            # Primer thumbnail suele estar a la izquierda-centro
            x = int(screen_w * 0.28)
            y = int(screen_h * 0.42)
            ui.click(x, y)
            time.sleep(1.5)

            # 2) Si no cargó, probar Enter (por si el foco ya estaba)
            ui.press("enter")
            time.sleep(0.8)

            # 3) Fallback: varios Tabs y Enter
            for _ in range(8):
                ui.press("tab")
                time.sleep(0.15)
            ui.press("enter")
        except Exception as error:
            print(f"[Desktop] No se pudo reproducir el primer video: {error}")

    def open_vscode(self, path="."):
        subprocess.Popen(["code", str(path)])

    def open_file_in_vscode(self, path, line=None):
        target = str(Path(path).resolve())
        subprocess.Popen(["code", "--goto", f"{target}:{line or 1}"])
