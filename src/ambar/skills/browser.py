import re
from urllib.parse import urlparse

from ambar.actions.desktop_controller import DesktopController
from ambar.skills.base import Skill


class BrowserSkill(Skill):
    def __init__(self, ai_manager=None):
        self.desktop = DesktopController()
        self._ai = ai_manager

    def can_execute(self, message):
        low = message.casefold()
        return "youtube" in low or "you tube" in low

    def execute(self, message):
        text, low = message.strip(), message.casefold()
        play_first = any(phrase in low for phrase in (
            "reproduce la primera", "reproduce el primero", "pon la primera",
            "pon el primero", "reproduce primero", "la primera opción", "la primera opcion",
        ))
        query = self._query_from(text, low)
        if not query:
            return "¿Qué quieres que busque en YouTube?"

        video_url = self._direct_video_url(query)
        if video_url:
            self.desktop.open_browser(video_url)
            return "Buscando en YouTube... Reproduciendo el video encontrado."

        self.desktop.search_youtube(query)
        self.desktop.play_first_youtube_result(wait_seconds=5)
        return (
            "No pude obtener el enlace con la IA, abro la búsqueda. "
            f"Buscando '{query}' en YouTube y reproduciendo la primera opción."
        )

    def _direct_video_url(self, query):
        if self._ai is None:
            return None
        prompt = (
            "Encuentra un video de YouTube para esta búsqueda: " + query + ". "
            "Responde estrictamente con una única URL de video en formato "
            "https://www.youtube.com/watch?v=..., sin texto adicional."
        )
        try:
            response = self._ai.generate_initiative(prompt)
        except Exception as error:
            print(f"[YouTube] No se pudo obtener URL directa: {error}")
            return None
        match = re.search(r"https?://[^\s)]+", response or "")
        return match.group(0).rstrip(".,!?") if match and self._is_youtube_video(match.group(0)) else None

    @staticmethod
    def _is_youtube_video(url):
        parsed = urlparse(url)
        host = parsed.netloc.casefold().removeprefix("www.")
        return (host == "youtube.com" and parsed.path == "/watch" and "v=" in parsed.query) or (
            host == "youtu.be" and bool(parsed.path.strip("/"))
        )

    @staticmethod
    def _query_from(text, low):
        query = text
        for marker in (
            "abre youtube y busca ", "abre you tube y busca ", "abre youtube ",
            "abre you tube ", "busca en youtube ", "busca youtube ", "youtube busca ",
        ):
            index = low.find(marker)
            if index >= 0:
                query = text[index + len(marker):]
                break
        for junk in (
            ", reproduce la primera", "reproduce la primera", ", reproduce el primero",
            "reproduce el primero", ", pon la primera", "pon la primera", "reproduce primero",
        ):
            index = query.casefold().find(junk)
            if index >= 0:
                query = query[:index]
        return query.strip(" .,")
