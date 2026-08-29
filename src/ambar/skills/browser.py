from ambar.actions.desktop_controller import DesktopController
from ambar.skills.base import Skill
class BrowserSkill(Skill):
    def __init__(self): self.desktop=DesktopController()
    def can_execute(self,message): return "youtube" in message.casefold()
    def execute(self,message):
        text,low=message.strip(),message.casefold(); play_first="reproduce la primera" in low; query=text
        for marker in ("abre youtube y busca ","abre youtube ","busca en youtube ","busca youtube "):
            index=low.find(marker)
            if index>=0: query=text[index+len(marker):]; break
        query=query.casefold().replace(", reproduce la primera","").replace("reproduce la primera","").strip(" .")
        if not query: return "¿Qué quieres que busque en YouTube?"
        self.desktop.search_youtube(query)
        if play_first: self.desktop.play_first_youtube_result(); return "Buscando en YouTube... Reproduciendo la primera opción."
        return "Buscando en YouTube..."