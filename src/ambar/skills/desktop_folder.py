import json
from pathlib import Path
from ambar.skills.base import Skill

class DesktopFolderSkill(Skill):
    def __init__(self):
        self.file=Path.home()/"AppData"/"Local"/"AMBAR"/"learned_skills.json"; self.file.parent.mkdir(parents=True,exist_ok=True)
        self.data=json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else {}; self.learning=None; self.waiting_name=False
    def can_execute(self,message):
        t=message.casefold()
        return self.learning is not None or self.waiting_name or ("escritorio" in t and "carpeta" in t and ("crea" in t or "crear" in t))
    def execute(self,message):
        t=message.strip(); low=t.casefold()
        if self.waiting_name:
            name=t.strip(' .')
            if not name: return "Necesito un nombre para la carpeta."
            path=Path.home()/"Desktop"/name; path.mkdir(parents=True,exist_ok=True); self.waiting_name=False
            return f"Carpeta creada correctamente: {path.name}."
        if self.learning is None and "escritorio" in low and "carpeta" in low:
            if self.data.get("desktop_folder"):
                self.waiting_name=True; return "Claro, ¿qué nombre tendrá la carpeta?"
            self.learning="offer"; return "No sé hacer eso todavía. ¿Deseas que aprenda a realizarlo?"
        if self.learning=="offer":
            if low in {"si","sí","si claro","sí claro"}: self.learning="steps"; return "Okey. Dime el paso a paso para abrir el escritorio y crear una carpeta. Di 'fin' al terminar."
            self.learning=None; return "Entendido, no aprenderé esa acción."
        if self.learning=="steps":
            if low=="fin":
                self.data["desktop_folder"]=True; self.file.write_text(json.dumps(self.data),encoding="utf-8"); self.learning=None
                return "Aprendí el flujo. La próxima vez crearé la carpeta y te pediré el nombre si falta."
            return "Paso guardado. Continúa o di fin."