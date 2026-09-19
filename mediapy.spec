# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the windowed onefile MediaPy binary.

yt-dlp is collected whole because it ships plugins and data files that
static analysis misses. If ./ffmpeg-bin holds static ffmpeg/ffprobe
(filled by the release workflow or a local build script), they are
embedded so the binary works without a system ffmpeg.
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("yt_dlp")

ffmpeg_dir = Path(SPECPATH) / "ffmpeg-bin"
if ffmpeg_dir.is_dir():
    suffix = ".exe" if sys.platform == "win32" else ""
    for tool in ("ffmpeg", "ffprobe"):
        path = ffmpeg_dir / (tool + suffix)
        if path.is_file():
            binaries.append((str(path), "."))

a = Analysis(
    ["main.py"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="mediapy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX-compressed binaries trigger antivirus false positives.
    upx=False,
    console=False,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="mediapy.app",
        icon=None,
        bundle_identifier=None,
    )
