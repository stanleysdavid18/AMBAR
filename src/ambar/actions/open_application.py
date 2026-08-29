import subprocess

from ambar.actions import Action


class OpenApplication(Action):

    def __init__(self, application):

        self.application = application

    def execute(self):
        try:
            subprocess.Popen(self.application)
        except OSError as error:
            raise RuntimeError(f"No se pudo abrir {self.application}") from error
