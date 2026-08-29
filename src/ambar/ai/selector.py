"""Selección y fallback de proveedores de texto para Ámbar."""

from time import monotonic


class AIUnavailableError(RuntimeError):
    pass


class ProviderSelector:
    """Prioriza proveedores cloud rápidos y deja Ollama como fallback local."""

    VALID_MODES = {"auto", "local", "cloud"}
    CLOUD_PRIORITY = ("groq", "gemini")

    def __init__(self, providers, mode="auto", connectivity=None, probe_ttl=60, clock=monotonic):
        if mode not in self.VALID_MODES:
            raise ValueError(f"Modo de IA desconocido: {mode}")
        self._providers, self._mode, self._connectivity = providers, mode, connectivity
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
                print(f"[AI] {name} falló ({error}); probando fallback.")
                self._health.pop(name, None)
                errors.append(f"{name}: {error}")
        raise AIUnavailableError("Ningún proveedor de IA respondió: " + "; ".join(errors))

    def _candidates(self):
        if self._mode == "local":
            return ["ollama"] if self._available("ollama") else []
        # No depende de api.openai.com: prueba los proveedores configurados directamente.
        cloud = []
        for name in self.CLOUD_PRIORITY:
            if self._available(name):
                cloud.append(name)
            else:
                print(f"[AI] {name} no está configurado o no está disponible; omitiendo.")
        if self._mode == "cloud":
            return cloud
        return [*cloud, *(["ollama"] if self._available("ollama") else [])]

    def _available(self, name):
        checked, now = self._health.get(name), self._clock()
        if checked and now - checked[0] < self._probe_ttl:
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