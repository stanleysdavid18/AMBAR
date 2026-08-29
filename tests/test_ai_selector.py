import unittest

from ambar.ai.selector import AIUnavailableError, ProviderSelector


class _Connectivity:
    def __init__(self, online=True): self.online = online
    def is_online(self): return self.online


class _Provider:
    def __init__(self, name, response=None, available=True, error=None):
        self.name, self.response, self.available, self.error, self.calls = name, response or name, available, error, 0
    def is_available(self): return self.available
    def generate(self, _history, _facts, _prompt):
        self.calls += 1
        if self.error: raise self.error
        return self.response


class ProviderSelectorTests(unittest.TestCase):
    def make_selector(self, *, mode="auto", online=True, groq=None, gemini=None, cerebras=None, ollama=None):
        return ProviderSelector(
            {
                "groq": groq or _Provider("groq"),
                "gemini": gemini or _Provider("gemini"),
                "cerebras": cerebras or _Provider("cerebras"),
                "ollama": ollama or _Provider("ollama"),
            },
            mode=mode, connectivity=_Connectivity(online),
        )

    def generate(self, selector): return selector.generate(history=[], facts={}, system_prompt="")

    def test_auto_tries_groq_even_when_generic_probe_is_offline(self):
        groq, local = _Provider("groq"), _Provider("ollama")
        self.assertEqual(self.generate(self.make_selector(online=False, groq=groq, ollama=local)), "groq")
        self.assertEqual(groq.calls, 1)

    def test_auto_falls_back_groq_to_gemini_to_cerebras_to_ollama(self):
        groq = _Provider("groq", error=ConnectionError("groq down"))
        gemini = _Provider("gemini", error=ConnectionError("gemini down"))
        cerebras = _Provider("cerebras", error=ConnectionError("cerebras down"))
        local = _Provider("ollama")
        self.assertEqual(self.generate(self.make_selector(groq=groq, gemini=gemini, cerebras=cerebras, ollama=local)), "ollama")
        self.assertEqual((groq.calls, gemini.calls, cerebras.calls, local.calls), (1, 1, 1, 1))

    def test_auto_prioritizes_groq_before_other_providers(self):
        groq, gemini, local = _Provider("groq"), _Provider("gemini"), _Provider("ollama")
        self.assertEqual(self.generate(self.make_selector(groq=groq, gemini=gemini, ollama=local)), "groq")
        self.assertEqual((groq.calls, gemini.calls, local.calls), (1, 0, 0))

    def test_local_and_cloud_modes_are_strict(self):
        groq, local = _Provider("groq"), _Provider("ollama")
        self.assertEqual(self.generate(self.make_selector(mode="local", groq=groq, ollama=local)), "ollama")
        self.assertEqual(self.generate(self.make_selector(mode="cloud", groq=groq, ollama=local)), "groq")

    def test_no_available_provider_returns_controlled_error(self):
        selector = self.make_selector(groq=_Provider("groq", available=False), gemini=_Provider("gemini", available=False), cerebras=_Provider("cerebras", available=False), ollama=_Provider("ollama", available=False))
        with self.assertRaises(AIUnavailableError): self.generate(selector)
