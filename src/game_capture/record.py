import threading
import time

import numpy as np
from loguru import logger

from src.game_capture.state.client import StateClient
from src.game_capture.video.pyav_capture import ImageStream
from src.utils.system_monitor import System_Monitor, track_runtime
from src.utils.save import save_bgr0_as_jpeg, save_state
from src.utils.load import load_yaml


class GameRecorder:
    """
    Bundles images and game state from Assetto Corsa and write them to disk
    """

    def __init__(self):
        self.__load_configuration()
        self.image_stream = ImageStream()
        self.state_capture = StateClient()
        self.is_running = True
        self.frame_counter = 0

    def __load_configuration(self):
        self._config = load_yaml("./src/config/record.yaml")
        self.root_dir = self._config["save_path"]

    def start(self):
        thread = threading.Thread(target=self._run)
        thread.start()

    def stop(self):
        self.is_running = False

    def _run(self):
        while self.is_running:
            image = self.image_stream.latest_bgr0_image
            state = self.state_capture.latest_state
            self._write_capture_to_file(image, state)
            self.frame_counter += 1

    @track_runtime
    def _write_capture_to_file(self, image: np.array, state: np.array):
        save_state(f"{self.root_dir}/{self.frame_counter}", state)
        save_bgr0_as_jpeg(f"{self.root_dir}/{self.frame_counter}", image)


# Benchmarking loop
def main():
    recorder = GameRecorder()
    n_frames = 900
    recorder.start()
    start_time = time.time()
    while recorder.frame_counter < n_frames:
        time.sleep(0.5)
    elapsed_time = time.time() - start_time
    recorder.stop()
    logger.info(
        f"Saved {recorder.frame_counter} frames in {elapsed_time}s {recorder.frame_counter/elapsed_time}fps"
    )
    System_Monitor.log_function_runtimes_times()


if __name__ == "__main__":
    main()