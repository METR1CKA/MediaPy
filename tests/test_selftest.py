import shutil
import sys

import pytest

from mediapy.download import resolve_ffmpeg, resolve_ffprobe


def test_bundled_tool_wins_over_path(tmp_path, monkeypatch):
    bundled = tmp_path / "ffmpeg"
    bundled.write_bytes(b"BIN")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    assert resolve_ffmpeg() == str(bundled)
    # ffprobe is not in the bundled dir, so the PATH copy is used instead.
    assert resolve_ffprobe() == "/usr/bin/ffprobe"


def test_falls_back_to_path_when_not_frozen(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.setattr(shutil, "which", lambda name: f"/opt/bin/{name}")

    assert resolve_ffmpeg() == "/opt/bin/ffmpeg"
    assert resolve_ffprobe() == "/opt/bin/ffprobe"


def test_missing_everywhere_returns_none(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.setattr(shutil, "which", lambda name: None)

    assert resolve_ffmpeg() is None
    assert resolve_ffprobe() is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_selftest_smoke(tmp_path, monkeypatch):
    from mediapy.selftest import selftest

    monkeypatch.chdir(tmp_path)

    assert selftest() == 0
    log = (tmp_path / "selftest.log").read_text(encoding="utf-8")
    assert "SELFTEST OK" in log
