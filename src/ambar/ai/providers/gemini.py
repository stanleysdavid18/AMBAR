"""Proveedor Gemini para la abstracción de IA existente de Ámbar."""

from ambar.config.secrets import ApiKeyStore


class GeminiProvider:
    def __init__(self, model, key_store=None):
        self.model = model
        self._keys = key_store or ApiKeyStore()
        self._client = None
        self._key_in_use = None
        self._error = None

    def is_available(self):
        key = self._keys.get("GEMINI_API_KEY")
        if not key:
            return False
        if self._error is not None and key == self._key_in_use:
            return False
        if self._client is not None and self._key_in_use is None:
            self._key_in_use = key
            return True
        if self._client is None or key != self._key_in_use:
            try:
                from google import genai
                self._client = genai.Client(api_key=key, vertexai=False)
                self._key_in_use, self._error = key, None
            except Exception as error:
                self._error = error
                return False
        return True

    def generate(self, history, facts, system_prompt=""):
        if not self.is_available():
            raise RuntimeError("Gemini no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}".strip()
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=self._contents_from_history(history),
                config={"system_instruction": instructions} if instructions else None,
            )
        except Exception as error:
            self._error = error
            raise
        text = getattr(response, "text", "")
        if not text:
            raise RuntimeError("Gemini no devolvió texto")
        return text.strip()

    @staticmethod
    def _contents_from_history(history):
        """Convierte mensajes OpenAI (role/content) al formato google-genai."""
        contents = []
        for message in history:
            text = str(message.get("content", "")).strip()
            if not text:
                continue
            role = "model" if message.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": text}]})
        if not contents:
            raise RuntimeError("Gemini necesita al menos un mensaje de usuario")
        return contents

