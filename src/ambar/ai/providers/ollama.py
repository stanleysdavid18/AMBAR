import os
import shutil
import subprocess
from pathlib import Path
from time import perf_counter, sleep, monotonic

from ollama import Client

from ambar.core.paths import application_root


class OllamaProvider:
    """
    Proveedor de IA usando Ollama.
    """

    def __init__(self, model="llama3.2:3b"):

        self.model = model
        self.client = Client()
        self._startup_attempted = False

        prompt_file = application_root() / "config" / "personality.txt"

        self.default_prompt = prompt_file.read_text(
            encoding="utf-8"
        )

    def generate(
        self,
        history,
        facts,
        system_prompt=""
    ):

        prompt = system_prompt or self.default_prompt

        messages = [

            {
                "role": "system",
                "content": prompt
            }

        ]

        if facts:

            facts_text = "Información conocida del usuario:\n\n"

            for key, value in facts.items():

                facts_text += f"{key}: {value}\n"

            messages.append(

                {
                    "role": "system",
                    "content": facts_text
                }

            )

        messages.extend(history)

        started = perf_counter()
        response = self.client.chat(
            model=self.model,
            messages=messages,
            keep_alive="30m",
        )
        print(f"[Ollama] Respuesta generada en {perf_counter() - started:.2f}s")

        return response["message"]["content"]

    def is_available(self):
        if self._responding():
            return True
        if self._startup_attempted:
            return False

        self._startup_attempted = True
        executable = self._find_executable()
        if executable is None:
            print("[Ollama] No se encontró ollama.exe; se usará un proveedor alternativo.")
            return False

        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(
                [str(executable), "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
        except OSError as error:
            print(f"[Ollama] No se pudo iniciar: {error}")
            return False

        deadline = monotonic() + 8
        while monotonic() < deadline:
            if self._responding():
                print("[Ollama] Servicio iniciado automáticamente.")
                return True
            sleep(0.25)
        print("[Ollama] No respondió tras iniciar; se usará un proveedor alternativo.")
        return False

    def _responding(self):
        try:
            self.client.list()
            return True
        except Exception:
            return False

    @staticmethod
    def _find_executable():
        from_path = shutil.which("ollama")
        candidates = [
            from_path,
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Ollama" / "ollama.exe",
        ]
        return next((Path(candidate) for candidate in candidates if candidate and Path(candidate).is_file()), None)
