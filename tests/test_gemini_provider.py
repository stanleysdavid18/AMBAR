import os
import unittest
from unittest.mock import patch

from ambar.ai.providers.gemini import GeminiProvider


class _Response:
    text = "  respuesta Gemini  "


class _Models:
    def __init__(self):
        self.call = None

    def generate_content(self, **kwargs):
        self.call = kwargs
        return _Response()


class _Client:
    def __init__(self):
        self.models = _Models()


class GeminiProviderTests(unittest.TestCase):
    def test_converts_openai_history_and_keeps_system_instruction(self):
        provider = GeminiProvider("gemini-2.5-flash")
        provider._client = _Client()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}):
            text = provider.generate(
                [{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "Hola, ¿en qué ayudo?"}],
                {"name": "Stanleys"},
                "Responde en español.",
            )
        self.assertEqual(text, "respuesta Gemini")
        self.assertEqual(provider._client.models.call["contents"], [
            {"role": "user", "parts": [{"text": "Hola"}]},
            {"role": "model", "parts": [{"text": "Hola, ¿en qué ayudo?"}]},
        ])
        self.assertIn("Responde en español.", provider._client.models.call["config"]["system_instruction"])
        self.assertIn("Stanleys", provider._client.models.call["config"]["system_instruction"])