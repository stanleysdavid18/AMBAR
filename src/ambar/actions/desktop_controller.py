from pathlib import Path
from urllib.parse import quote_plus
import os
import shutil
import subprocess
import time
class DesktopController:
    def _ui(self):
        import pyautogui; pyautogui.PAUSE=0.15; return pyautogui
    def _browser(self):
        candidates=[shutil.which("brave"), Path(os.environ.get("ProgramFiles", r"C:\Program Files"))/"BraveSoftware"/"Brave-Browser"/"Application"/"brave.exe", shutil.which("chrome"), "chrome.exe"]
        return next((str(item) for item in candidates if item and (not isinstance(item, Path) or item.is_file())), "chrome.exe")
    def open_browser(self,url): subprocess.Popen([self._browser(),url]); time.sleep(10)
    def search_youtube(self,query): self.open_browser("https://www.youtube.com/results?search_query="+quote_plus(query))
    def play_first_youtube_result(self,wait_seconds=12): time.sleep(wait_seconds); ui=self._ui(); ui.press("tab"); ui.press("enter")
    def open_vscode(self,path="."): subprocess.Popen(["code",str(path)])
    def open_file_in_vscode(self,path,line=None): subprocess.Popen(["code","--goto",f"{Path(path).resolve()}:{line or 1}"])