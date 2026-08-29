"""Proveedor Gemini para la abstracción de IA existente de Ambar."""

import os


class GeminiProvider:
    def __init__(self, model):
        self.model, self._client, self._error = model, None, None

    def is_available(self):
        if not os.environ.get("GEMINI_API_KEY"): return False
        if self._client is None and self._error is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            except Exception as error:
                self._error = error
                return False
        return self._client is not None

    def generate(self, history, facts, system_prompt=""):
        if not self.is_available(): raise RuntimeError("Gemini no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}"
        response = self._client.models.generate_content(model=self.model, contents=history, config={"system_instruction": instructions} if instructions else None)
        text = getattr(response, "text", "")
        if not text: raise RuntimeError("Gemini no devolvió texto")
        return text.strip()
