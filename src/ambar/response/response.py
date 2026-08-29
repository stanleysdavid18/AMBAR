from dataclasses import dataclass, field


@dataclass
class Response:
    """
    Respuesta generada por Ámbar.
    """

    text: str

    speak: bool = True

    emotion: str = "neutral"

    actions: list = field(default_factory=list)

    metadata: dict = field(default_factory=dict)