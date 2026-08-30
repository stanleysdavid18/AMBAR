# Instalar Ámbar betaV2

## Requisitos

- Windows 10 u 11 de 64 bits.
- Micrófono funcional y con permisos para aplicaciones de escritorio.
- Modo local: Ollama instalado y un modelo local disponible.
- Modo cloud propio: al menos una API key propia guardada desde ⚙️.

En el primer inicio selecciona **Modo local** o **Modo cloud propio**. Sin IA, las skills locales como abrir aplicaciones siguen funcionando.

## Modo desarrollador / pruebas

No está recomendado para usuarios finales. Es experimental, puede dejar de funcionar y no incluye OAuth de producción. Solo se habilita al confirmar el aviso y se configura con un archivo local no versionado:

`config/dev_secrets.json`

Contenido permitido (reemplaza valores de ejemplo solo en tu equipo):

```json
{
  "GROQ_API_KEY": "...",
  "GEMINI_API_KEY": "...",
  "CEREBRAS_API_KEY": "..."
}
```

No distribuyas ese archivo ni uses keys de producción en builds de prueba.

## Generar distribución e instalador

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging\Ambar_betaV2.spec
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\Ambar_betaV2.iss
```

La distribución queda en `dist\Ambar_betaV2\` y el instalador esperado en `installer\output\Ambar_betaV2_Setup.exe`.

Si PyInstaller falla por una dependencia de Whisper, Torch o Piper, conserva `packaging\Ambar_betaV2.spec`, instala la dependencia indicada en el error dentro de `.venv` y vuelve a ejecutar el segundo comando.
