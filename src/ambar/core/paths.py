import os
import sys
from pathlib import Path


def application_root() -> Path:
    """Ubicación de recursos tanto en desarrollo como en PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[3]


def writable_runtime() -> Path:
    """Carpeta escribible para audio y diagnósticos del usuario actual."""
    if getattr(sys, "frozen", False):
        root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AMBAR"
    else:
        root = application_root()
    runtime = root / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    return runtime


def writable_config_root() -> Path:
    """Configuración persistente fuera del bundle cuando la app está congelada."""
    if getattr(sys, "frozen", False):
        root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AMBAR" / "config"
    else:
        root = application_root() / "config"
    root.mkdir(parents=True, exist_ok=True)
    return root
