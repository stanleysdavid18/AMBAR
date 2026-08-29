from ambar.ai.providers.cerebras import CerebrasProvider
from ambar.ai.providers.gemini import GeminiProvider
from ambar.ai.providers.groq import GroqProvider
from ambar.ai.providers.ollama import OllamaProvider
from ambar.ai.providers.openai import OpenAIProvider
from ambar.ai.selector import ProviderSelector
from ambar.ai.connectivity import ConnectivityChecker
from ambar.config.manager import ConfigManager
from ambar.memory.working_memory import WorkingMemory
from ambar.memory.facts_memory import FactsMemory
from ambar.memory.extractor import FactExtractor


class AIManager:
    """Administra el proveedor de IA."""

    def __init__(self):
        self.config = ConfigManager()
        self.memory = WorkingMemory()
        self.facts = FactsMemory()
        self.extractor = FactExtractor(self.facts)

        ai_config = self.config.get("ai")
        self.providers = {
            "ollama": OllamaProvider(ai_config["ollama_model"]),
            "openai": OpenAIProvider(ai_config["openai_model"]),
            "gemini": GeminiProvider(ai_config["gemini_model"]),
            "groq": GroqProvider(ai_config["groq_model"]),
            "cerebras": CerebrasProvider(ai_config["cerebras_model"]),
        }
        self.selector = ProviderSelector(
            self.providers,
            mode=ai_config.get("mode", "auto"),
            priority=ai_config.get("provider_priority"),
            connectivity=ConnectivityChecker(),
            probe_ttl=ai_config.get("probe_cache_seconds", 60),
        )

    def generate(self, message: str, system_prompt: str = "") -> str:
        self.memory.add("user", message)
        self.extractor.process(message)
        text = message.lower().strip()
        if text in ["como me llamo", "cómo me llamo", "cual es mi nombre", "cuál es mi nombre"]:
            name = self.facts.get("name")
            response = f"Claro 😊 Tu nombre es {name}." if name else "Todavía no sé cómo te llamas."
        else:
            response = self.selector.generate(
                history=self.memory.history(), facts=self.facts.all(), system_prompt=system_prompt
            )
        self.memory.add("assistant", response)
        return response

    def generate_initiative(self, instruction: str, system_prompt: str = "") -> str:
        """Genera una iniciativa sin registrarla falsamente como mensaje del usuario."""
        history = self.memory.history() + [{"role": "user", "content": instruction}]
        return self.selector.generate(history=history, facts=self.facts.all(), system_prompt=system_prompt)
