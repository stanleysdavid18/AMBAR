"""Proveedor Groq adaptado de proyecto-ambar."""

import os


class GroqProvider:
    """Cliente reutilizable de Groq con la misma interfaz que los demás proveedores."""

    def __init__(self, model):
        self.model = model
        self._client = None
        self._error = None

    def is_available(self):
        if not os.environ.get("GROQ_API_KEY"):
            return False
        if self._client is None and self._error is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=os.environ["GROQ_API_KEY"])
            except Exception as error:
                self._error = error
                return False
        return self._client is not None

    def generate(self, history, facts, system_prompt=""):
        if not self.is_available():
            raise RuntimeError("Groq no está configurado o no está disponible")
        instructions = system_prompt
        if facts:
            facts_text = "\n".join(f"{key}: {value}" for key, value in facts.items())
            instructions = f"{instructions}\n\nInformación conocida del usuario:\n{facts_text}"
        messages = []
        if instructions:
            messages.append({"role": "system", "content": instructions})
        messages.extend(history)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=700,
        )
        text = response.choices[0].message.content
        if not text:
            raise RuntimeError("Groq no devolvió texto")
        return text.strip()