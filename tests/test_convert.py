import subprocess
from pathlib import Path

import pytest

from mediapy.convert import to_mp3
from mediapy.errors import ConvertError, MissingFFmpeg


@pytest.fixture(autouse=True)
def fake_ffmpeg(monkeypatch):
    monkeypatch.setattr("mediapy.convert.ensure_ffmpeg", lambda: "/usr/bin/ffmpeg")


def make_run(captured=None):
    def run(cmd, check, capture_output, text):
        if captured is not None:
            captured.append(cmd)
        Path(cmd[-1]).write_bytes(b"MP3")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    return run


def test_success_replaces_dest_atomically(tmp_path, monkeypatch):
    video = tmp_path / "song.mp4"
    video.write_bytes(b"VIDEO")
    dest = tmp_path / "song.mp3"
    dest.write_bytes(b"OLD")
    captured = []
    monkeypatch.setattr(subprocess, "run", make_run(captured))

    result = to_mp3(video, dest)

    assert result == dest
    assert dest.read_bytes() == b"MP3"
    assert not (tmp_path / "song.tmp.mp3").exists()
    cmd = captured[0]
    for flag in ("-vn", "-acodec", "libmp3lame", "-q:a", "2"):
        assert flag in cmd
    assert str(video) in cmd


def test_ffmpeg_failure_raises_convert_error_with_stderr(tmp_path, monkeypatch):
    video = tmp_path / "song.mp4"
    video.write_bytes(b"VIDEO")
    dest = tmp_path / "song.mp3"
    dest.write_bytes(b"OLD")

    def failing_run(cmd, check, capture_output, text):
        raise subprocess.CalledProcessError(1, cmd, stderr="boom")

    monkeypatch.setattr(subprocess, "run", failing_run)
    with pytest.raises(ConvertError, match="boom"):
        to_mp3(video, dest)
    assert dest.read_bytes() == b"OLD"


def test_spawn_failure_raises_convert_error(tmp_path, monkeypatch):
    video = tmp_path / "song.mp4"
    video.write_bytes(b"VIDEO")
    dest = tmp_path / "song.mp3"

    def failing_run(cmd, check, capture_output, text):
        raise OSError("cannot spawn")

    monkeypatch.setattr(subprocess, "run", failing_run)
    with pytest.raises(ConvertError, match="cannot spawn"):
        to_mp3(video, dest)


def test_missing_ffmpeg(tmp_path, monkeypatch):
    def boom():
        raise MissingFFmpeg("ffmpeg was not found in PATH.")

    monkeypatch.setattr("mediapy.convert.ensure_ffmpeg", boom)
    with pytest.raises(MissingFFmpeg):
        to_mp3(tmp_path / "song.mp4", tmp_path / "song.mp3")
