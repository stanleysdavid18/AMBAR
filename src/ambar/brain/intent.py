from enum import Enum


class Intent(Enum):
    CHAT = "chat"
    SHOW_MEMORY = "show_memory"
    SHOW_FACTS = "show_facts"
    GET_TIME = "get_time"
    GET_DATE = "get_date"
    UNKNOWN = "unknown"