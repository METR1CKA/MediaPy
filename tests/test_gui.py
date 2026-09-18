tk = None

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    pass

import pytest

if tk is None:
    pytest.skip("tkinter is not available", allow_module_level=True)

import mediapy.gui as gui
from mediapy.app import Job, Mode, Progress
from mediapy.errors import InvalidName, InvalidUrl, MissingFFmpeg, PathNotSelected


@pytest.fixture
def root():
    try:
        r = tk.Tk()
    except tk.TclError:
        pytest.skip("no display")
    yield r
    r.destroy()


def log_text(win):
    return win._log.get("1.0", "end")


def test_build_job_strips_url_and_keeps_name(tmp_path):
    job = gui.build_job("  https://youtu.be/x  ", "song.mp4", tmp_path, Mode.VIDEO)
    assert job == Job(
        url="https://youtu.be/x", name="song.mp4", out_dir=tmp_path, mode=Mode.VIDEO
    )


def test_build_job_empty_url_raises(tmp_path):
    with pytest.raises(InvalidUrl):
        gui.build_job("   ", "song", tmp_path, Mode.VIDEO)


def test_build_job_missing_folder_raises():
    with pytest.raises(PathNotSelected):
        gui.build_job("https://youtu.be/x", "song", None, Mode.VIDEO)


def test_build_job_invalid_name_raises(tmp_path):
    with pytest.raises(InvalidName):
        gui.build_job("https://youtu.be/x", "%", tmp_path, Mode.VIDEO)


def test_build_job_dot_dot_name_raises(tmp_path):
    with pytest.raises(InvalidName):
        gui.build_job("https://youtu.be/x", "..", tmp_path, Mode.VIDEO)


def test_multipoint_name_is_sanitized_only_once(monkeypatch, tmp_path):
    import mediapy.app as app

    class FakeDownloader:
        def download(self, url, dest, **kwargs):
            return dest

    monkeypatch.setattr(app, "ensure_ffmpeg", lambda: "/usr/bin/ffmpeg")
    monkeypatch.setattr(app, "Downloader", FakeDownloader)

    job = gui.build_job("https://youtu.be/x", "mi.video.final", tmp_path, Mode.VIDEO)
    assert job.name == "mi.video.final"
    result = app.run(job)
    assert result == tmp_path / "mi.video.mp4"


@pytest.fixture
def make_window(root, monkeypatch):
    monkeypatch.setattr(gui, "ensure_ffmpeg", lambda: "/usr/bin/ffmpeg")

    def _make(runner):
        return gui.MediaPyWindow(root, runner=runner)

    return _make


def test_window_download_flow(make_window, tmp_path):
    jobs = []

    def runner(job, *, on_status, on_progress):
        jobs.append(job)
        on_status("Working...")
        on_progress(Progress("Video stream", 5, 10))
        on_progress(Progress("Audio stream", 0, 0))
        on_progress(Progress("Audio stream", 10, 10))
        return tmp_path / "out.mp4"

    win = make_window(runner)
    win._url_var.set("https://youtu.be/x")
    win._name_var.set("out")
    win._set_out_dir(tmp_path)
    win._mode_var.set(str(Mode.VIDEO_AND_MP3))

    win._on_download()
    assert win._worker is not None
    win._worker.join(5)
    win._poll()

    expected = Job(
        url="https://youtu.be/x", name="out", out_dir=tmp_path, mode=Mode.VIDEO_AND_MP3
    )
    assert jobs == [expected]
    log = log_text(win)
    assert "Working..." in log
    assert f"Guardado: {tmp_path / 'out.mp4'}" in log
    assert not win._download_btn.instate(["disabled"])
    assert float(win._bar.cget("value")) == 0.0
    assert str(win._bar.cget("mode")) == "determinate"


def test_apply_progress_transitions_bar(make_window):
    win = make_window(lambda job, *, on_status, on_progress: None)
    win._apply_progress(Progress("Video stream", 5, 10))
    assert str(win._bar.cget("mode")) == "determinate"
    assert float(win._bar.cget("value")) == 50.0
    win._apply_progress(Progress("Audio stream", 0, 0))
    assert str(win._bar.cget("mode")) == "indeterminate"
    win._apply_progress(Progress("Audio stream", 10, 10))
    assert str(win._bar.cget("mode")) == "determinate"
    assert float(win._bar.cget("value")) == 100.0
    win._end_run()
    assert float(win._bar.cget("value")) == 0.0
    assert str(win._bar.cget("mode")) == "determinate"


def test_window_error_flow(make_window, tmp_path):
    def runner(job, *, on_status, on_progress):
        raise ValueError("boom")

    win = make_window(runner)
    win._url_var.set("https://youtu.be/x")
    win._name_var.set("out")
    win._set_out_dir(tmp_path)

    win._on_download()
    win._worker.join(5)
    win._poll()

    assert "[ ! ] boom" in log_text(win)
    assert not win._download_btn.instate(["disabled"])


def test_missing_ffmpeg_disables_download(root, monkeypatch):
    def raise_missing():
        raise MissingFFmpeg("no ffmpeg")

    monkeypatch.setattr(gui, "ensure_ffmpeg", raise_missing)
    win = gui.MediaPyWindow(root)
    assert win._download_btn.instate(["disabled"])
    assert "no ffmpeg" in log_text(win)


def test_invalid_form_logs_error_without_worker(make_window, tmp_path):
    def runner(job, *, on_status, on_progress):
        raise AssertionError("runner must not be called")

    win = make_window(runner)

    win._on_download()
    assert win._worker is None
    assert "[ ! ]" in log_text(win)

    win._url_var.set("https://youtu.be/x")
    win._on_download()
    assert win._worker is None

    win._set_out_dir(tmp_path)
    win._name_var.set("%")
    win._on_download()
    assert win._worker is None
