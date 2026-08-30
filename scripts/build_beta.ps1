param([switch]$Installer)
$ErrorActionPreference = "Stop"
$python = ".\.venv\Scripts\python.exe"
& $python -m PyInstaller --noconfirm --clean packaging\Ambar_betaV2.spec
if ($Installer) {
    & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\Ambar_betaV2.iss
}
