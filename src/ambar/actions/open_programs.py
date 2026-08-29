"""Enumeración y cierre normal de ventanas visibles de Windows."""
import ctypes
from difflib import SequenceMatcher


class OpenProgramController:
    WM_CLOSE = 0x0010

    def list_open_programs(self):
        windows = []
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def collect(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if not length:
                return True
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, len(title))
            process_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            if process_id.value == kernel32.GetCurrentProcessId():
                return True
            windows.append({"hwnd": hwnd, "pid": process_id.value, "title": title.value.strip()})
            return True

        user32.EnumWindows(collect, 0)
        unique = {}
        for window in windows:
            unique.setdefault(window["pid"], window)
        return list(unique.values())

    def close(self, program):
        """Solicita cierre normal; no fuerza procesos ni pierde datos silenciosamente."""
        return bool(ctypes.windll.user32.PostMessageW(program["hwnd"], self.WM_CLOSE, 0, 0))

    @staticmethod
    def match(programs, choice):
        choice = choice.casefold().strip()
        if choice.isdigit():
            index = int(choice) - 1
            return programs[index] if 0 <= index < len(programs) else None
        best, score = None, 0.0
        for program in programs:
            title = program["title"].casefold()
            candidate = max(SequenceMatcher(None, choice, title).ratio(), 1.0 if choice in title else 0.0)
            if candidate > score:
                best, score = program, candidate
        return best if score >= 0.45 else None