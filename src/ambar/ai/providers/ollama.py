from time import perf_counter

from ollama import Client

from ambar.core.paths import application_root


class OllamaProvider:
    """
    Proveedor de IA usando Ollama.
    """

    def __init__(self, model="llama3.2:3b"):

        self.model = model
        self.client = Client()

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
        self.client.list()
        return True
