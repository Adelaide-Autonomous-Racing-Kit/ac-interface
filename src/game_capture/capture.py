from src.game_capture.state.client import StateClient
from src.game_capture.video.pyav_capture import ImageStream


class GameCapture:
    def __init__(self):
        self.image_stream = ImageStream()
        self.state_capture = StateClient()
        self.capture = None

    def run(self):
        for image in self.image_stream:
            state = self.state_capture.game_state
            self.capture = (image, state)

    