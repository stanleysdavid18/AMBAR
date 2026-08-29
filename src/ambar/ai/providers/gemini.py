"""Proveedor Gemini para la abstracción de IA existente de Ámbar."""

import os


class GeminiProvider:
    def __init__(self, model):
        self.model, self._client, self._error = model, None, None

    def is_available(self):
        if not os.environ.get("GEMINI_API_KEY"):
            return False
        if self._client is None and self._error is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], vertexai=False)
            except Exception as error:
                self._error = error
                return False
        return self._client is not None

    def generate(self, history, facts, system_prompt=""):
        if not self.is_available():
            raise RuntimeError("Gemini no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}".strip()
        response = self._client.models.generate_content(
            model=self.model,
            contents=self._contents_from_history(history),
            config={"system_instruction": instructions} if instructions else None,
        )
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