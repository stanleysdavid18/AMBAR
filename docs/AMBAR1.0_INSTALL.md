# AMBAR 1.0 para Windows

Ejecuta `AMBAR1.0.exe` desde la carpeta distribuida. No muevas ni borres las
subcarpetas internas: contienen Piper y los modelos de voz.

## Requisito de IA

AMBAR usa Ollama como servidor local de conversación. En cada equipo de destino
instala Ollama y descarga el modelo configurado una sola vez:

```powershell
ollama pull llama3.2:3b
```

Después inicia Ollama o verifica que su servicio esté activo. La aplicación
incluye Whisper `small`, Piper y su voz, por lo que no descarga modelos de voz.

## Diagnóstico

El último audio capturado se guarda en:

```text
%LOCALAPPDATA%\AMBAR\runtime\audio\debug.wav
```

El mismo directorio contiene los WAV temporales generados por Piper.
