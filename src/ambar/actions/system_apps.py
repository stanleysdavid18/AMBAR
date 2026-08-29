"""Búsqueda conservadora de accesos a programas instalados en Windows."""
from difflib import SequenceMatcher
from pathlib import Path
import os


class SystemApplicationFinder:
    def find(self, requested):
        requested = requested.casefold().strip()
        candidates = []
        for path in self._app_paths():
            candidates.append((path.stem, str(path)))
        for root in self._start_menu_roots():
            if root.exists():
                for path in root.rglob("*.lnk"):
                    candidates.append((path.stem, str(path)))
        best = None
        for name, command in candidates:
            score = SequenceMatcher(None, requested, name.casefold()).ratio()
            if requested in name.casefold():
                score += 0.25
            if best is None or score > best["score"]:
                best = {"name": name, "command": command, "score": score}
        return best if best and best["score"] >= 0.65 else None

    @staticmethod
    def _start_menu_roots():
        yield Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        yield Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    @staticmethod
    def _app_paths():
        try:
            import winreg
        except ImportError:
            return []
        paths = []
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r"Software\Microsoft\Windows\CurrentVersion\App Paths") as key:
                    index = 0
                    while True:
                        try:
                            name = winreg.EnumKey(key, index)
                            with winreg.OpenKey(key, name) as app_key:
                                command, _ = winreg.QueryValueEx(app_key, None)
                                paths.append(Path(command))
                            index += 1
                        except OSError:
                            break
            except OSError:
                continue
        return paths