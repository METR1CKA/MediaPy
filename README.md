# MediaPy

Descarga videos de YouTube como MP4 o MP3 con una ventana gráfica.

## Descargar

Baja el binario para tu sistema desde la página de [Releases](https://github.com/METR1CKA/MediaPy/releases). **ffmpeg va incluido dentro del binario**, no hace falta instalarlo.

| Sistema | Archivo |
| --- | --- |
| Windows (64 bits) | `mediapy-windows-amd64.exe` |
| macOS (Apple Silicon) | `mediapy-macos-arm64.zip` |
| macOS (Intel) | `mediapy-macos-intel.zip` |
| Linux (64 bits) | `mediapy-linux-amd64` |

- **macOS**: al abrirlo por primera vez, Gatekeeper puede bloquearlo por ser de un desarrollador no identificado. Haz clic derecho sobre `mediapy.app` y elige «Abrir».
- **Windows**: SmartScreen puede mostrar «Windows protegió tu PC». Pulsa «Más información» → «Ejecutar de todas formas».
- **Linux**: da permisos de ejecución (`chmod +x mediapy-linux-amd64`) y ejecútalo. Requiere glibc 2.35 o superior.

## Requisitos

- Python >= 3.12
- pip
- **ffmpeg** en el PATH (requerido para fusionar y convertir). Instálalo con `brew install ffmpeg` (macOS) o `apt install ffmpeg` (Linux/WSL).
- **tkinter** (incluido en macOS/Windows; en Linux: `sudo apt install python3-tk`). La ventana necesita un entorno con display (no funciona sobre SSH sin escritorio gráfico).

## Instalación

1. Crear VENV (opcional)

```console
python3 -m venv venv
source venv/bin/activate
```

2. Instalar

```console
python -m pip install -e .
```

## Uso

Abre la ventana de descarga:

```console
python main.py
```

1. Pega la URL del video.
2. Escribe un nombre para el archivo.
3. Elige la carpeta de destino con el botón «Elegir carpeta…».
4. Selecciona el modo: **Video (MP4)**, **Video + MP3** (conserva ambos) o **Solo audio (MP3)**.
5. Pulsa «Descargar» y sigue el progreso en la barra y el registro.

Si falta ffmpeg, la ventana lo avisa al abrir y el botón «Descargar» queda deshabilitado hasta instalarlo.

## Desarrollo

```console
python -m pip install -e ".[dev]"
python -m pytest
```

## Publicar una versión

1. Sube los cambios a `main`.
2. Crea y sube un tag:

```console
git tag v3.1.0
git push origin v3.1.0
```

Al empujar el tag, el workflow construye los cuatro binarios (Windows, macOS Apple Silicon, macOS Intel y Linux), verifica cada uno con `--selftest` y los publica en una release.

Para probar el empaquetado sin publicar nada, ejecuta el workflow **Release** desde la pestaña Actions con «Run workflow»: los binarios quedarán como artefactos de la ejecución.
