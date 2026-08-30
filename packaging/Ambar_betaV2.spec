# PyInstaller onedir spec for Ambar_betaV2.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH).parent
hiddenimports = collect_submodules("faster_whisper") + collect_submodules("silero_vad")
datas = [
    (str(root / "config" / "settings.json"), "config"),
    (str(root / "config" / "personality.txt"), "config"),
    (str(root / "models"), "models"),
    (str(root / "assets"), "assets"),
]
datas += collect_data_files("faster_whisper")

a = Analysis(
    [str(root / "src" / "ambar" / "__main__.py")], pathex=[str(root / "src")], binaries=[], datas=datas,
    hiddenimports=hiddenimports, excludes=["tests"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="Ambar_betaV2",
    icon=str(root / "assets" / "icon.ico"), console=False,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="Ambar_betaV2")
