"""Política de automatización: permite herramientas concretas, no comandos arbitrarios."""
from pathlib import Path

class AutomationPolicy:
    ALLOWED={"open_application","open_url","youtube_search_and_play","open_vscode_project","open_vscode_file","capture_screen","create_desktop_folder"}
    CONFIRM_REQUIRED={"delete_file","move_file","run_shell","install_package","change_system_settings","send_data"}
    def authorize(self, action, path=None):
        if action in self.CONFIRM_REQUIRED: return False, "Esta acción requiere confirmación explícita."
        if action not in self.ALLOWED: return False, "Acción no permitida."
        if path:
            allowed=(Path.home()/"Desktop", Path.home()/"Documents", Path.home()/"AppData"/"Local"/"AMBAR")
            try:
                resolved=Path(path).resolve()
                if not any(resolved.is_relative_to(root.resolve()) for root in allowed): return False, "Ruta fuera de las ubicaciones permitidas."
            except OSError: return False, "Ruta no válida."
        return True, "Autorizada"