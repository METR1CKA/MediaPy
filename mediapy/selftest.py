"""Headless selftest: verifies imports, ffmpeg resolution and conversion.

Written for frozen binaries, where a failed window would prove nothing, so
results go to selftest.log in the working directory instead of the console.
"""

import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from mediapy import __version__
from mediapy.convert import to_mp3
from mediapy.download import resolve_ffmpeg, resolve_ffprobe
from mediapy.errors import MediaPyError
from mediapy.paths import safe_stem


def selftest() -> int:
    checks: list[tuple[str, Callable[[], str]]] = []

    def yt_dlp_check() -> str:
        import yt_dlp

        return yt_dlp.version.__version__

    checks.append(("yt-dlp import", yt_dlp_check))

    def ffmpeg_check() -> str:
        ffmpeg = resolve_ffmpeg()
        if ffmpeg is None:
            raise RuntimeError("ffmpeg not found (bundled or PATH)")
        # LGPL static builds ship both tools; a frozen binary missing
        # ffprobe cannot extract audio, so treat it as broken.
        if getattr(sys, "frozen", False) and resolve_ffprobe() is None:
            raise RuntimeError("bundled ffprobe missing")
        return ffmpeg

    checks.append(("ffmpeg available", ffmpeg_check))

    def conversion_check() -> str:
        ffmpeg = resolve_ffmpeg()
        if ffmpeg is None:
            raise RuntimeError("ffmpeg not found (bundled or PATH)")
        with tempfile.TemporaryDirectory() as td:
            video = Path(td) / "selftest.mp4"
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=duration=0.5:size=128x96:rate=10",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=0.5",
                    # Native encoders: the bundled LGPL builds have no libx264.
                    "-c:v",
                    "mpeg4",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(video),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            audio = Path(td) / "selftest.mp3"
            to_mp3(video, audio)
            size = audio.stat().st_size
            if size < 1000:
                raise RuntimeError(f"mp3 too small: {size} bytes")
        return f"mp3 {size} bytes"

    checks.append(("mp4 to mp3 conversion", conversion_check))

    def paths_check() -> str:
        if safe_stem("song.mp4") != "song":
            raise AssertionError("safe_stem did not strip the extension")
        for bad in ("", "%", ".."):
            try:
                safe_stem(bad)
            except MediaPyError:
                continue
            raise AssertionError(f"safe_stem accepted {bad!r}")
        return "ok"

    checks.append(("name validation", paths_check))

    lines = [f"MediaPy {__version__} selftest"]
    ok = True
    for name, fn in checks:
        try:
            detail = fn()
            lines.append(f"OK    {name}: {detail}")
        except Exception as e:
            ok = False
            lines.append(f"FAIL  {name}: {e}")
    lines.append("SELFTEST " + ("OK" if ok else "FAIL"))
    report = "\n".join(lines)
    print(report)
    try:
        Path("selftest.log").write_text(report + "\n", encoding="utf-8")
    except OSError:
        pass
    return 0 if ok else 1
