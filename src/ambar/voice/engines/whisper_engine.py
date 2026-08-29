from faster_whisper import WhisperModel

from ambar.core.paths import application_root


class WhisperEngine:
    """
    Motor de reconocimiento de voz utilizando Faster-Whisper.

    Configurado para conversación en español.
    """

    def __init__(self):

        print("[Whisper] Cargando modelo...")

        bundled_model = application_root() / "models" / "whisper-small"
        model = bundled_model if bundled_model.exists() else "small"
        self.model = WhisperModel(
            str(model),
            device="cpu",
            compute_type="int8"
        )

        print("[Whisper] Modelo listo.")

    def transcribe(self, audio_file: str) -> str:

        print("[Whisper] Transcribiendo...")

        segments, info = self.model.transcribe(

            audio_file,

            language="es",

            task="transcribe",

            beam_size=1,

            best_of=1,

            temperature=0,

            patience=1,

            vad_filter=True,

            vad_parameters={

                "min_silence_duration_ms": 700,

                "speech_pad_ms": 250

            },

            condition_on_previous_text=False,

            compression_ratio_threshold=2.4,

            log_prob_threshold=-1.0,

            no_speech_threshold=0.55,

            initial_prompt="Conversación en español. La palabra de activación es Ámbar. Hola Ámbar.",

            hotwords="Ámbar, Ambar, hola Ámbar",

        )

        print(
            f"[Whisper][debug] Idioma detectado: {info.language} | "
            f"confianza: {getattr(info, 'language_probability', 0.0):.3f}"
        )

        segments = list(segments)
        print(f"[Whisper][debug] Segmentos generados: {len(segments)}")

        pieces = []
        discarded = []

        for index, segment in enumerate(segments, start=1):

            raw_text = segment.text.strip()
            no_speech_prob = getattr(segment, "no_speech_prob", 0.0)
            print(
                f"[Whisper][debug] Segmento {index}: "
                f"{segment.start:.2f}-{segment.end:.2f}s | "
                f"no_speech_prob: {no_speech_prob:.3f} | texto: {raw_text!r}"
            )

            # Ignorar segmentos que Whisper considera silencio
            if no_speech_prob > 0.55:
                if raw_text:
                    discarded.append(raw_text)
                continue

            text = raw_text

            if not text:
                continue

            pieces.append(text)

        if not pieces and discarded:
            print(
                "[Whisper][debug] Todos los segmentos con texto fueron "
                "descartados por no_speech_prob; se conserva la transcripción."
            )
            pieces = discarded

        text = " ".join(pieces).strip()

        print(f"[Whisper] Escuché: {text}")

        return text
