import os


class OpenAIProvider:
    """Cliente reutilizable de OpenAI mediante Responses API."""

    def __init__(self, model):
        self.model = model
        self._client = None
        self._error = None

    def is_available(self):
        if not os.environ.get("OPENAI_API_KEY"):
            return False
        if self._client is None and self._error is None:
            try:
                from openai import OpenAI
                self._client = OpenAI()
            except Exception as error:
                self._error = error
                return False
        if self._client is None:
            return False
        self._client.models.list()
        return True

    def generate(self, history, facts, system_prompt=""):
        if self._client is None and not self.is_available():
            raise RuntimeError("OpenAI no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}"
        response = self._client.responses.create(
            model=self.model,
            instructions=instructions or None,
            input=history,
            store=False,
        )
        if not response.output_text:
            raise RuntimeError("OpenAI no devolvió texto")
        return response.output_text
