#define MyAppName "Ámbar"
#define MyAppVersion "betaV2"
#define MyAppExeName "Ambar_betaV2.exe"

[Setup]
AppId={{D9AF0440-F24C-4A91-9F69-2C4412E2E6B5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Ámbar
DefaultDirName={localappdata}\Ambar_betaV2
DefaultGroupName=Ámbar
DisableProgramGroupPage=yes
OutputDir=installer\output
OutputBaseFilename=Ambar_betaV2_Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\Ambar_betaV2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Ámbar"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Ámbar"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Ámbar"; Flags: nowait postinstall skipifsilent
