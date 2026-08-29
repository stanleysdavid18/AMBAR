class ContextManager:
    """
    Mantiene el contexto actual de la conversación.
    """

    def __init__(self):

        self.data = {}

    def set(self, key, value):

        self.data[key] = value

    def get(self, key, default=None):

        return self.data.get(key, default)

    def clear(self):

        self.data.clear()

    def all(self):

        return self.data