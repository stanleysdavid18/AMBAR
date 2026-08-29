from enum import Enum, auto


class SystemState(Enum):
    """
    Estados posibles del sistema Ámbar.
    """

    OFFLINE = auto()
    STARTING = auto()
    READY = auto()
    SLEEPING = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    ERROR = auto()
