# MediaPy

- Python >= 3.11
- pip

## Ejecutar programa en modo dev

1. Crear VENV

```console
python -m venv venv
```

2. Correr requirements

```console
python -m pip install -r requirements.txt
```

3. Ejecutar

```console
python main.py
```

## Archivo ejecutable para windows

En caso de tener error al iniciar el programa y que este no se ejecute, puedes hacer lo siguiente

1. Copiar el contenido dentro de [audio.txt](output/audio.txt) y pegarlo a la siguiente ruta

```txt
C:\Users\{USER}\AppData\Local\Programs\Python\{Python-version}\Lib\site-packages\moviepy\audio\fx\all\__init__.py
```

2. Copiar el contenido dentro de [video.txt](output/video.txt) y pegarlo a la siguiente ruta

```txt
C:\Users\{USER}\AppData\Local\Programs\Python\{Python-version}\Lib\site-packages\moviepy\video\fx\all\__init__.py
```

3. Ya puedes utilizar el archivo [main.exe](output/main.exe)
