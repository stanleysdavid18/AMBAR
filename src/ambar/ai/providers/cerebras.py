"""Proveedor Cerebras mediante la API compatible con OpenAI."""

from openai import OpenAI

from ambar.config.secrets import ApiKeyStore


class CerebrasProvider:
    def __init__(self, model, key_store=None):
        self.model = model
        self._keys = key_store or ApiKeyStore()
        self._client = None
        self._key_in_use = None
        self._error = None

    def is_available(self):
        key = self._keys.get("CEREBRAS_API_KEY")
        if not key:
            return False
        if self._error is not None and key == self._key_in_use:
            return False
        if self._client is None or key != self._key_in_use:
            try:
                self._client = OpenAI(
                    api_key=key,
                    base_url="https://api.cerebras.ai/v1",
                    timeout=15.0,
                )
                self._key_in_use, self._error = key, None
            except Exception as error:
                self._error = error
                return False
        return True

    def generate(self, history, facts, system_prompt=""):
        if not self.is_available():
            raise RuntimeError("Cerebras no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}".strip()
        messages = []
        if instructions:
            messages.append({"role": "system", "content": instructions})
        messages.extend(history)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=700,
            )
        except Exception as error:
            self._error = error
            raise
        text = response.choices[0].message.content
        if not text:
            raise RuntimeError("Cerebras no devolvió texto")
        return text.strip()
