class WorkingMemory:
    """
    Memoria temporal de la conversación actual.
    """

    def __init__(self, max_messages=16):
        self.messages = []
        self.max_messages = max_messages

    def add(self, role: str, content: str):
        """
        Guarda un mensaje.
        """

        self.messages.append(
            {
                "role": role,
                "content": content
            }
        )
        if len(self.messages) > self.max_messages:
            del self.messages[:-self.max_messages]

    def history(self):
        """
        Devuelve toda la conversación.
        """

        return list(self.messages)

    def clear(self):
        """
        Borra la memoria.
        """

        self.messages.clear()
