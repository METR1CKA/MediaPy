from pathlib import Path

from mediapy.errors import InvalidName


def safe_stem(name: str) -> str:
    if not name or ".." in name or "%" in name:
        raise InvalidName("Name must not be empty or contain '..' or '%'.")
    stem = Path(Path(name).name).stem
    if not stem:
        raise InvalidName("Name does not contain a usable file name.")
    return stem
