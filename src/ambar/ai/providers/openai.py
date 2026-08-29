from openai import OpenAI

from ambar.config.secrets import ApiKeyStore


class OpenAIProvider:
    """Cliente reutilizable de OpenAI mediante Responses API."""

    def __init__(self, model, key_store=None):
        self.model = model
        self._keys = key_store or ApiKeyStore()
        self._client = None
        self._key_in_use = None
        self._error = None

    def is_available(self):
        key = self._keys.get("OPENAI_API_KEY")
        if not key:
            return False
        if self._error is not None and key == self._key_in_use:
            return False
        if self._client is None or key != self._key_in_use:
            try:
                self._client = OpenAI(api_key=key, timeout=15.0)
                self._key_in_use, self._error = key, None
            except Exception as error:
                self._error = error
                return False
        return True

    def generate(self, history, facts, system_prompt=""):
        if not self.is_available():
            raise RuntimeError("OpenAI no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}"
        try:
            response = self._client.responses.create(
                model=self.model,
                instructions=instructions or None,
                input=history,
                store=False,
            )
        except Exception as error:
            self._error = error
            raise
        if not response.output_text:
            raise RuntimeError("OpenAI no devolvió texto")
        return response.output_text
