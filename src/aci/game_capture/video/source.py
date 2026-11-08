"""Select an image source without importing desktop capture for direct frames."""

from .game_frame import GameFrameStream


class DesktopFrameStream:
    def __init__(self, config):
        from .pyav_capture import ImageStream

        self._stream = ImageStream(config)

    def read_latest(self):
        if not self._stream.is_stale:
            return self._stream.image, None
        return None

    def close(self):
        self._stream.stop()


def open_image_source(config):
    images = config["images"]
    backend = images.get("backend", "desktop")
    if backend == "desktop":
        return DesktopFrameStream(config)
    if backend == "game_frame":
        return GameFrameStream(images)
    raise ValueError(f"Unknown image backend: {backend!r}")
