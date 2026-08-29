from ambar.personality.profile import PersonalityProfile


class PersonalityManager:
    """
    Gestiona la personalidad de Ámbar.
    """

    def __init__(self):
        self.profile = PersonalityProfile()

    def get_name(self):
        return self.profile.name

    def get_prompt(self):
        """
        Devuelve la personalidad completa.

        Más adelante este texto será enviado
        al modelo de IA.
        """

        return f"""
Nombre: {self.profile.name}

Descripción:
{self.profile.description}

Personalidad:
{self.profile.personality}

Origen:
{self.profile.origin}

Forma de hablar:
{self.profile.tone}

Objetivo:
{self.profile.goal}
"""