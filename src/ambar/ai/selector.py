"""Selección y fallback de proveedores de texto para Ámbar."""

from time import monotonic


class AIUnavailableError(RuntimeError):
    pass


class ProviderSelector:
    """Prioriza proveedores cloud y deja Ollama como fallback local."""

    VALID_MODES = {"auto", "local", "cloud"}
    DEFAULT_PRIORITY = ("groq", "gemini", "cerebras", "ollama")

    def __init__(self, providers, mode="auto", priority=None, connectivity=None, probe_ttl=60, clock=monotonic):
        if mode not in self.VALID_MODES:
            raise ValueError(f"Modo de IA desconocido: {mode}")
        self._providers, self._mode, self._connectivity = providers, mode, connectivity
        requested = priority or self.DEFAULT_PRIORITY
        self._priority = tuple(name for name in requested if name in providers)
        self._probe_ttl, self._clock, self._health, self._latency = float(probe_ttl), clock, {}, {}

    @property
    def mode(self):
        return self._mode

    def generate(self, *, history, facts, system_prompt=""):
        errors = []
        for name in self._candidates():
            try:
                print(f"[AI] Usando proveedor: {name}")
                started = self._clock()
                response = self._providers[name].generate(history, facts, system_prompt)
                self._latency[name] = self._clock() - started
                return response
            except Exception as error:
                print(f"[AI] {name} falló ({self._error_summary(error)}); probando fallback.")
                self._health.pop(name, None)
                errors.append(name)
        raise AIUnavailableError("Ningún proveedor de IA respondió: " + ", ".join(errors))

    @staticmethod
    def _error_summary(error):
        message = " ".join(str(error).split())
        return f"{type(error).__name__}: {message[:180]}" if message else type(error).__name__

    def _candidates(self):
        if self._mode == "local":
            return ["ollama"] if self._available("ollama") else []
        cloud = [name for name in self._priority if name != "ollama" and self._available(name)]
        if self._mode == "cloud":
            return cloud
        return [*cloud, *(["ollama"] if self._available("ollama") else [])]

    def _available(self, name):
        checked, now = self._health.get(name), self._clock()
        if checked and checked[1] and now - checked[0] < self._probe_ttl:
            return checked[1]
        provider = self._providers.get(name)
        if provider is None:
            return False
        try:
            available = bool(provider.is_available())
        except Exception:
            available = False
        self._health[name] = (now, available)
        return available

