"""Proveedor Groq para la abstracción de IA existente de Ámbar."""

from ambar.config.secrets import ApiKeyStore


class GroqProvider:
    def __init__(self, model, key_store=None):
        self.model = model
        self._keys = key_store or ApiKeyStore()
        self._client = None
        self._key_in_use = None
        self._error = None

    def _key(self):
        key = self._keys.get("GROQ_API_KEY")
        if key != self._key_in_use:
            if self._client is not None and self._key_in_use is None:
                self._key_in_use = key  # permite clientes inyectados en pruebas
            else:
                self._client, self._error, self._key_in_use = None, None, key
        return key

    def is_available(self):
        key = self._key()
        if not key:
            return False
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=key, timeout=15.0)
            except Exception as error:
                self._error = error
                return False
        return True

    def generate(self, history, facts, system_prompt=""):
        if not self.is_available():
            raise RuntimeError("Groq no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}".strip()
        messages = ([{"role": "system", "content": instructions}] if instructions else []) + list(history)
        try:
            response = self._client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, max_tokens=700,
            )
        except Exception as error:
            self._client, self._error = None, error
            raise
        text = response.choices[0].message.content
        if not text:
            raise RuntimeError("Groq no devolvió texto")
        return text.strip()
