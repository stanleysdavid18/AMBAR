class FactsMemory:
    """
    Almacena hechos importantes del usuario.
    """

    def __init__(self):
        self.facts = {}

    def set(self, key: str, value: str):
        self.facts[key] = value

    def get(self, key: str):
        return self.facts.get(key)

    def all(self):
        return self.facts