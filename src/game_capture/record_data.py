from src.game_capture.pyav_capture import ImageStream


class DataRecorder:
    def __init__(self):
        self._image_stream = ImageStream()
