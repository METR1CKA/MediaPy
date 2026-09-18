class MediaPyError(Exception):
    pass


class MissingFFmpeg(MediaPyError):
    pass


class DownloadError(MediaPyError):
    pass


class ConvertError(MediaPyError):
    pass


class PathNotSelected(MediaPyError):
    pass


class InvalidName(MediaPyError):
    pass


class InvalidUrl(MediaPyError):
    pass
