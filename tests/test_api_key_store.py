import tempfile
import unittest

from pathlib import Path

from ambar.config.secrets import ApiKeyStore


class _Settings:
    def __init__(self): self.values = {}
    def value(self, key, default=""): return self.values.get(key, default)
    def setValue(self, key, value): self.values[key] = value
    def sync(self): pass


class ApiKeyStoreTests(unittest.TestCase):
    def test_dev_secret_is_used_only_when_testing_mode_is_enabled(self):
        settings = _Settings()
        secrets_file = Path(tempfile.mkdtemp()) / "dev_secrets.json"
        secrets_file.write_text('{"GEMINI_API_KEY": "dev-key"}', encoding="utf-8")
        store = ApiKeyStore(settings=settings, environ={"GEMINI_API_KEY": "env-key"}, dev_secrets_path=secrets_file)
        self.assertEqual(store.get("GEMINI_API_KEY"), "env-key")
        settings.setValue("developer/testing_mode", True)
        self.assertEqual(store.get("GEMINI_API_KEY"), "dev-key")
    def test_saved_key_has_priority_over_environment_and_is_masked(self):
        settings = _Settings()
        store = ApiKeyStore(settings=settings, environ={"GROQ_API_KEY": "env-value"})
        store.save({"GROQ_API_KEY": "saved-secret-1234"})
        self.assertEqual(store.get("GROQ_API_KEY"), "saved-secret-1234")
        self.assertEqual(ApiKeyStore.mask(store.get("GROQ_API_KEY")), "sav…1234")

