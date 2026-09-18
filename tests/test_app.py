import pytest

import mediapy.app as app
from mediapy.app import Job, Mode, Progress, run
from mediapy.errors import MissingFFmpeg

BASE = "https://youtu.be/x"


@pytest.fixture(autouse=True)
def stubs(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "ensure_ffmpeg", lambda: "/usr/bin/ffmpeg")
    state = {"downloads": [], "conversions": [], "statuses": [], "progress": []}

    class FakeDownloader:
        def download(
            self,
            url,
            dest,
            *,
            audio_only=False,
            progress_hook=None,
            postprocessor_hook=None,
        ):
            state["downloads"].append(
                {
                    "url": url,
                    "dest": dest,
                    "audio_only": audio_only,
                    "progress_hook": progress_hook,
                    "postprocessor_hook": postprocessor_hook,
                }
            )
            if progress_hook is not None:
                progress_hook(
                    {
                        "status": "downloading",
                        "downloaded_bytes": 5,
                        "total_bytes": 10,
                        "info_dict": {"vcodec": "none", "acodec": "mp4a"},
                    }
                )
                progress_hook({"status": "finished"})
            if postprocessor_hook is not None:
                postprocessor_hook(
                    {"status": "started", "postprocessor": "FFmpegExtractAudio"}
                )
            return dest

    def fake_to_mp3(video, dest):
        state["conversions"].append((video, dest))
        return dest

    monkeypatch.setattr(app, "Downloader", FakeDownloader)
    monkeypatch.setattr(app, "to_mp3", fake_to_mp3)

    def on_status(text):
        state["statuses"].append(text)

    def on_progress(progress):
        state["progress"].append(progress)

    state["on_status"] = on_status
    state["on_progress"] = on_progress
    return state


def test_video_mode_downloads_mp4(stubs, tmp_path):
    result = run(
        Job(url=BASE, name="song", out_dir=tmp_path, mode=Mode.VIDEO),
        on_status=stubs["on_status"],
        on_progress=stubs["on_progress"],
    )
    mp4 = tmp_path / "song.mp4"
    assert result == mp4
    assert len(stubs["downloads"]) == 1
    d = stubs["downloads"][0]
    assert d["url"] == BASE
    assert d["dest"] == mp4
    assert d["audio_only"] is False
    assert d["progress_hook"] is not None
    assert d["postprocessor_hook"] is None
    assert stubs["conversions"] == []
    assert stubs["statuses"] == ["Downloading video...", f"Saved: {mp4}"]
    assert stubs["progress"] == [Progress("Audio stream", 5, 10)]


def test_video_and_mp3_mode_downloads_and_converts(stubs, tmp_path):
    result = run(
        Job(url=BASE, name="song", out_dir=tmp_path, mode=Mode.VIDEO_AND_MP3),
        on_status=stubs["on_status"],
        on_progress=stubs["on_progress"],
    )
    mp4 = tmp_path / "song.mp4"
    mp3 = tmp_path / "song.mp3"
    assert result == mp4
    d = stubs["downloads"][0]
    assert d["dest"] == mp4
    assert d["audio_only"] is False
    assert d["postprocessor_hook"] is None
    assert stubs["conversions"] == [(mp4, mp3)]
    assert stubs["statuses"] == [
        "Downloading video...",
        f"Saved: {mp4}",
        "Converting to MP3...",
        f"Saved: {mp3}",
    ]
    assert stubs["progress"] == [
        Progress("Audio stream", 5, 10),
        Progress("Converting to MP3", 0, None),
    ]
    assert stubs["progress"][-1].fraction is None


def test_audio_only_mode_downloads_mp3(stubs, tmp_path):
    result = run(
        Job(url=BASE, name="song", out_dir=tmp_path, mode=Mode.AUDIO_ONLY),
        on_status=stubs["on_status"],
        on_progress=stubs["on_progress"],
    )
    mp3 = tmp_path / "song.mp3"
    assert result == mp3
    d = stubs["downloads"][0]
    assert d["dest"] == mp3
    assert d["audio_only"] is True
    assert d["progress_hook"] is not None
    assert d["postprocessor_hook"] is not None
    assert stubs["conversions"] == []
    assert stubs["statuses"] == [
        "Downloading audio...",
        "Post-processing (FFmpegExtractAudio)...",
        f"Saved: {mp3}",
    ]
    assert stubs["progress"] == [Progress("Audio stream", 5, 10)]
    assert stubs["progress"][0].fraction == 0.5


def test_name_is_sanitized_to_stem(stubs, tmp_path):
    run(
        Job(url=BASE, name="song.mp4", out_dir=tmp_path, mode=Mode.AUDIO_ONLY),
        on_status=stubs["on_status"],
        on_progress=stubs["on_progress"],
    )
    assert stubs["downloads"][0]["dest"] == tmp_path / "song.mp3"


def test_missing_ffmpeg_propagates(stubs, monkeypatch, tmp_path):
    def raise_missing():
        raise MissingFFmpeg("no ffmpeg found")

    monkeypatch.setattr(app, "ensure_ffmpeg", raise_missing)
    with pytest.raises(MissingFFmpeg):
        run(Job(url=BASE, name="song", out_dir=tmp_path, mode=Mode.VIDEO))
