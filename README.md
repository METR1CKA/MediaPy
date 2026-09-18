# MediaPy

Descarga videos de YouTube como MP4 o MP3 con una ventana gráfica.

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
