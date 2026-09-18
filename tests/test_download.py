import os
import time
from pathlib import Path
from unittest import mock

import pytest
import yt_dlp

from mediapy.download import Downloader
from mediapy.errors import DownloadError


class FakeYDL:
    def __init__(self, opts=None):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def run_download(
    tmp_path,
    dest_name,
    tmp_files=(),
    filepath=None,
    audio_only=False,
    exc=None,
    progress_hook=None,
    postprocessor_hook=None,
):
    dest = tmp_path / dest_name
    captured = {}

    class YDL(FakeYDL):
        def __init__(self, opts=None):
            super().__init__(opts)
            captured["opts"] = opts

        def extract_info(self, url, download=True):
            if exc is not None:
                raise exc
            for name in tmp_files:
                (tmp_path / name).write_bytes(b"NEW")
            return {"filepath": str(tmp_path / filepath)} if filepath else {}

    with mock.patch.object(yt_dlp, "YoutubeDL", YDL):
        result = Downloader().download(
            "https://youtu.be/x",
            dest,
            audio_only=audio_only,
            progress_hook=progress_hook,
            postprocessor_hook=postprocessor_hook,
        )
    return dest, result, captured["opts"]


def touch_future(path, seconds=3600):
    future = time.time() + seconds
    os.utime(path, (future, future))


def test_video_opts(tmp_path):
    dest, _, opts = run_download(tmp_path, "song.mp4", tmp_files=["song.tmp.mp4"])
    assert opts["noplaylist"] is True
    assert opts["format"] == "bv*+ba/b"
    assert opts["merge_output_format"] == "mp4"
    assert "postprocessors" not in opts
    assert dest.read_bytes() == b"NEW"


def test_audio_only_opts(tmp_path):
    dest, _, opts = run_download(
        tmp_path, "song.mp3", tmp_files=["song.tmp.mp3"], audio_only=True
    )
    assert opts["format"] == "bestaudio/best"
    assert opts["postprocessors"][0]["preferredcodec"] == "mp3"
    assert opts["postprocessors"][0]["preferredquality"] == "192"
    assert dest.exists()


def test_filepath_reported(tmp_path):
    dest, result, _ = run_download(
        tmp_path, "song.mp4", tmp_files=["song.tmp.mp4"], filepath="song.tmp.mp4"
    )
    assert result == dest
    assert dest.exists()


def test_glob_fallback(tmp_path):
    dest, result, _ = run_download(tmp_path, "clip.mp4", tmp_files=["clip.tmp.mp4"])
    assert result == dest
    assert dest.exists()


def test_glob_fallback_escapes_metacharacters(tmp_path):
    dest, result, _ = run_download(
        tmp_path, "song[1].mp4", tmp_files=["song[1].tmp.mp4"]
    )
    assert result == dest
    assert dest.exists()


def test_nothing_produced(tmp_path):
    with pytest.raises(DownloadError):
        run_download(tmp_path, "ghost.mp4")


def test_failure_preserves_dest(tmp_path):
    dest = tmp_path / "keep.mp4"
    dest.write_bytes(b"ORIGINAL")
    with pytest.raises(DownloadError):
        run_download(tmp_path, "keep.mp4", exc=OSError("disk full"))
    assert dest.read_bytes() == b"ORIGINAL"


def test_yt_dlp_error_is_wrapped(tmp_path):
    with pytest.raises(DownloadError, match="boom"):
        run_download(tmp_path, "song.mp4", exc=yt_dlp.utils.DownloadError("boom"))


def test_stale_tmp_is_not_promoted(tmp_path):
    stale = tmp_path / "stale.tmp.mp4"
    stale.write_bytes(b"STALE")
    with pytest.raises(DownloadError):
        run_download(tmp_path, "stale.mp4")
    assert not stale.exists()


def test_stale_name_reused_by_new_download_wins(tmp_path):
    stale = tmp_path / "stale.tmp.mp4"
    stale.write_bytes(b"STALE")
    dest, result, _ = run_download(tmp_path, "stale.mp4", tmp_files=["stale.tmp.mp4"])
    assert result == dest
    assert dest.read_bytes() == b"NEW"


def test_newer_stale_tmp_does_not_beat_fresh_download(tmp_path):
    stale = tmp_path / "song.tmp.f137.mp4"
    stale.write_bytes(b"STALE")
    touch_future(stale)
    dest, result, _ = run_download(tmp_path, "song.mp4", tmp_files=["song.tmp.mp4"])
    assert result == dest
    assert dest.read_bytes() == b"NEW"


def test_cleanup_removes_leftover_tmp(tmp_path):
    dest, result, _ = run_download(
        tmp_path,
        "song.mp4",
        tmp_files=["song.tmp.mp4", "song.tmp.f137.mp4"],
        filepath="song.tmp.mp4",
    )
    assert result == dest
    assert not (tmp_path / "song.tmp.f137.mp4").exists()


def test_cleanup_escapes_metacharacters(tmp_path):
    leftover = tmp_path / "song[1].tmp.mp4"
    leftover.write_bytes(b"LEFTOVER")
    dest = tmp_path / "song[1].mp4"

    class Boom(FakeYDL):
        def extract_info(self, url, download=True):
            raise yt_dlp.utils.DownloadError("nope")

    with mock.patch.object(yt_dlp, "YoutubeDL", Boom):
        with pytest.raises(DownloadError):
            Downloader().download("u", dest)
    assert not leftover.exists()


def test_hooks_are_injected_into_ydl_opts(tmp_path):
    ph = lambda data: None
    pph = lambda data: None
    _, _, opts = run_download(
        tmp_path,
        "song.mp4",
        tmp_files=["song.tmp.mp4"],
        progress_hook=ph,
        postprocessor_hook=pph,
    )
    assert opts["progress_hooks"] == [ph]
    assert opts["postprocessor_hooks"] == [pph]


def test_no_hooks_leaves_keys_absent(tmp_path):
    _, _, opts = run_download(tmp_path, "song.mp4", tmp_files=["song.tmp.mp4"])
    assert "progress_hooks" not in opts
    assert "postprocessor_hooks" not in opts
