import time
from ambar.actions.desktop_controller import DesktopController
from ambar.skills.base import Skill

class BrowserSkill(Skill):
    def __init__(self): self.desktop=DesktopController()
    def can_execute(self,message): return "youtube" in message.casefold()
    def execute(self,message):
        text=message.strip(); low=text.casefold()
        query=text
        for marker in ("abre youtube y ", "abre youtube ", "busca en youtube ", "busca youtube ", "pon ", "reproduce "):
            if marker in low:
                index=low.index(marker)+len(marker); query=text[index:].strip(); break
        query=query.replace("reproduce", "").replace("en youtube", "").strip(' .')
        if not query: return "¿Qué quieres que busque en YouTube?"
        self.desktop.search_youtube(query)
        time.sleep(3)
        ui=self.desktop._ui(); ui.press("tab"); ui.press("enter")
        return f"Claro, con mucho gusto. Buscando y reproduciendo {query} en YouTube."