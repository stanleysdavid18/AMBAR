import re


class TextNormalizer:
    """
    Prepara el texto para que Piper lo pronuncie mejor.
    """

    def normalize(self, text: str) -> str:

        # Eliminar emojis y caracteres fuera del rango ASCII/Latino básico
        text = re.sub(r"[^\w\s.,;:!?¿¡áéíóúÁÉÍÓÚñÑ()-]", "", text)

        # Reemplazar saltos de línea
        text = text.replace("\n", ". ")

        # Espacios múltiples
        text = re.sub(r"\s+", " ", text)

        return text.strip()