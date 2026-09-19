import glob
import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from mediapy.errors import DownloadError, MissingFFmpeg


def _bundled_dir() -> Path | None:
    base = getattr(sys, "_MEIPASS", None)
    return Path(base) if base else None


def _resolve_tool(name: str) -> str | None:
    bundled = _bundled_dir()
    if bundled is not None:
        candidate = bundled / (name + (".exe" if os.name == "nt" else ""))
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def resolve_ffmpeg() -> str | None:
    return _resolve_tool("ffmpeg")


def resolve_ffprobe() -> str | None:
    return _resolve_tool("ffprobe")


def ensure_ffmpeg() -> str:
    ffmpeg = resolve_ffmpeg()
    if ffmpeg is None:
        raise MissingFFmpeg(
            "ffmpeg was not found. Frozen builds bundle it; for source "
            "installs add it to PATH (brew install ffmpeg / apt install "
            "ffmpeg) and try again."
        )
    return ffmpeg


Hook = Callable[[dict[str, Any]], None]


class Downloader:
    def download(
        self,
        url: str,
        dest: Path,
        *,
        audio_only: bool = False,
        progress_hook: Hook | None = None,
        postprocessor_hook: Hook | None = None,
    ) -> Path:
        tmp_tmpl = str(dest.parent / f"{dest.stem}.tmp.%(ext)s")
        ydl_opts: dict[str, Any] = {
            "noplaylist": True,
            "outtmpl": tmp_tmpl,
        }
        if progress_hook is not None:
            ydl_opts["progress_hooks"] = [progress_hook]
        if postprocessor_hook is not None:
            ydl_opts["postprocessor_hooks"] = [postprocessor_hook]
        ffmpeg = resolve_ffmpeg()
        if ffmpeg is not None:
            ydl_opts["ffmpeg_location"] = str(Path(ffmpeg).parent)
        if audio_only:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        else:
            ydl_opts["format"] = "bv*+ba/b"
            ydl_opts["merge_output_format"] = "mp4"
        self._cleanup_tmp(dest)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            produced = self._produced(dest, info)
            return produced.replace(dest)
        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(str(e)) from e
        except OSError as e:
            raise DownloadError(str(e)) from e
        finally:
            self._cleanup_tmp(dest)

    @staticmethod
    def _produced(dest: Path, info: dict[str, Any] | None) -> Path:
        filepath = info.get("filepath") if info else None
        if filepath and Path(filepath).exists():
            return Path(filepath)
        pattern = f"{glob.escape(dest.stem)}.tmp*"
        candidates = [
            p
            for p in dest.parent.glob(pattern)
            if p.is_file() and p.suffix == dest.suffix
        ]
        if not candidates:
            raise DownloadError(
                f"Download finished but no output file was found for {dest.stem!r}."
            )
        return max(candidates, key=lambda p: p.stat().st_mtime)

    @staticmethod
    def _cleanup_tmp(dest: Path) -> None:
        pattern = f"{glob.escape(dest.stem)}.tmp*"
        for p in dest.parent.glob(pattern):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
