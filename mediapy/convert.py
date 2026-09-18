import subprocess
from pathlib import Path

from mediapy.download import ensure_ffmpeg
from mediapy.errors import ConvertError


def to_mp3(video: Path, dest: Path) -> Path:
    ffmpeg = ensure_ffmpeg()
    tmp = dest.with_name(f"{dest.stem}.tmp{dest.suffix}")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-q:a",
        "2",
        str(tmp),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return tmp.replace(dest)
    except subprocess.CalledProcessError as e:
        raise ConvertError(e.stderr.strip() or str(e)) from e
    except OSError as e:
        raise ConvertError(str(e)) from e
