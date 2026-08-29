from ambar.memory.facts_memory import FactsMemory


class FactExtractor:

    def __init__(self, memory: FactsMemory):
        self.memory = memory

    def process(self, message: str):

        text = message.lower()

        if text.startswith("me llamo "):

            name = message[9:].strip()

            self.memory.set("name", name)