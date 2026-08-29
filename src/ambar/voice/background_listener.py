import queue
import threading

from ambar.voice.listener import Listener


class BackgroundListener:
    """
    Escucha continuamente en segundo plano.

    Filtra transcripciones vacías o claramente inválidas
    antes de enviarlas a ConversationService.
    """

    def __init__(self, listener=None):

        self.listener = listener or Listener()

        self.queue = queue.Queue()

        self.running = False

        self.thread = None

        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Longitud mínima aceptada
        self._min_length = 2

    # =============================

    def _valid_text(self, text):

        if not text:
            return False

        text = text.strip()

        if len(text) < self._min_length:
            return False

        # Solo signos
        if all(not c.isalnum() for c in text):
            return False

        return True

    # =============================

    def _listen_loop(self):
        try:
            while self.running:
                try:
                    text = self.listener.listen(self._stop_event)
                except Exception as error:
                    if self.running:
                        print(f"[Voice] capture/transcription error: {error}")
                    break
                if not self.running:
                    break
                if self._valid_text(text):
                    self.queue.put(text)
        finally:
            with self._lock:
                self.running = False

    # =============================

    def start(self):

        with self._lock:
            if self.running:
                return True
            if self.thread and self.thread.is_alive():
                return False

            self.running = True
            self._stop_event.clear()
            self.thread = threading.Thread(
                target=self._listen_loop,
                daemon=True,
                name="ambar-listener",
            )
            self.thread.start()
            return True

    # =============================

    def stop(self):

        with self._lock:
            self.running = False
            self._stop_event.set()
            thread = self.thread

        if thread and thread.is_alive():
            thread.join(timeout=2)

        stopped = not thread or not thread.is_alive()
        if not stopped:
            print("[Voz] El listener no terminó; se evita crear otra instancia.")
        if stopped and thread:
            self.thread = None
        return stopped

    # =============================

    def get_message(self, timeout=None):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None
