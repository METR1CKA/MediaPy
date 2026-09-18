from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from mediapy.convert import to_mp3
from mediapy.download import Downloader, ensure_ffmpeg
from mediapy.paths import safe_stem


class Mode(StrEnum):
    VIDEO = "video"
    VIDEO_AND_MP3 = "video_and_mp3"
    AUDIO_ONLY = "audio_only"


@dataclass(frozen=True, slots=True)
class Job:
    url: str
    name: str
    out_dir: Path
    mode: Mode


@dataclass(frozen=True, slots=True)
class Progress:
    """A single download step. `total` is None when the size is unknown."""

    label: str
    downloaded: int
    total: int | None

    @property
    def fraction(self) -> float | None:
        if not self.total:
            return None
        return min(self.downloaded / self.total, 1.0)


StatusCb = Callable[[str], None]
ProgressCb = Callable[[Progress], None]


def _noop(_: object) -> None:
    pass


def run(
    job: Job,
    *,
    on_status: StatusCb = _noop,
    on_progress: ProgressCb = _noop,
) -> Path:
    """Download the job and return the path of the file the user asked for."""
    ensure_ffmpeg()
    stem = safe_stem(job.name)
    downloader = Downloader()
    hook = _ProgressReporter(on_status, on_progress)

    if job.mode is Mode.AUDIO_ONLY:
        audio = job.out_dir / f"{stem}.mp3"
        on_status("Downloading audio...")
        downloader.download(
            job.url,
            audio,
            audio_only=True,
            progress_hook=hook.on_download,
            postprocessor_hook=hook.on_postprocess,
        )
        on_status(f"Saved: {audio}")
        return audio

    video = job.out_dir / f"{stem}.mp4"
    on_status("Downloading video...")
    downloader.download(job.url, video, progress_hook=hook.on_download)
    on_status(f"Saved: {video}")

    if job.mode is Mode.VIDEO_AND_MP3:
        audio = job.out_dir / f"{stem}.mp3"
        on_status("Converting to MP3...")
        on_progress(Progress("Converting to MP3", 0, None))
        to_mp3(video, audio)
        on_status(f"Saved: {audio}")

    return video


class _ProgressReporter:
    """Translates yt-dlp hook payloads into `Progress` and status messages.

    Runs on the worker thread, so it must never touch widgets.
    """

    def __init__(self, on_status: StatusCb, on_progress: ProgressCb) -> None:
        self._on_status = on_status
        self._on_progress = on_progress
        self._step = 0

    def on_download(self, data: dict) -> None:
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            self._on_progress(
                Progress(
                    label=self._label(data),
                    downloaded=data.get("downloaded_bytes") or 0,
                    total=total,
                )
            )
        elif status == "finished":
            # A merged download reports "finished" once per stream, so each one
            # starts a new 0-100% step instead of continuing the previous bar.
            self._step += 1

    def on_postprocess(self, data: dict) -> None:
        if data.get("status") == "started":
            self._on_status(f"Post-processing ({data.get('postprocessor', '?')})...")

    def _label(self, data: dict) -> str:
        info = data.get("info_dict") or {}
        vcodec = info.get("vcodec")
        acodec = info.get("acodec")
        if vcodec and vcodec != "none":
            return "Video stream"
        if acodec and acodec != "none":
            return "Audio stream"
        return f"Stream {self._step + 1}"
