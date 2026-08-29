"""Comprobaciones de red ligeras y fáciles de sustituir en pruebas."""

import socket


class ConnectivityChecker:
    def __init__(self, host="api.openai.com", port=443, timeout=1.5):
        self.host = host
        self.port = port
        self.timeout = timeout

    def is_online(self):
        try:
            with socket.create_connection((self.host, self.port), self.timeout):
                return True
        except OSError:
            return False
