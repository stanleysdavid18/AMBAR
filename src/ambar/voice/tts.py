class TextToSpeech:
    """
    Motor de síntesis de voz.

    Por ahora simplemente devuelve el texto.
    Más adelante utilizará Piper.
    """

    def speak(self, text: str):

        print(f"🔊 {text}")