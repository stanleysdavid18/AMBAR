from dataclasses import dataclass, field


@dataclass
class BrainResponse:
    """
    Respuesta generada por el Brain.
    """

    text: str

    speak: bool = True

    remember: bool = True

    emotion: str = "neutral"

    actions: list = field(default_factory=list)