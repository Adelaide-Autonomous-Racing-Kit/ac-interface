import threading
import time

from loguru import logger
import numpy as np
from src.config.constants import RECORD_CONFIG_FILE
from src.game_capture.state.client import StateClient
from src.game_capture.video.pyav_capture import ImageStream
from src.utils.load import load_yaml
from src.utils.save import save_bgr0_as_jpeg, save_bytes, save_state
from src.utils.system_monitor import System_Monitor, track_runtime


class GameRecorder:
    """
    Bundles images and game state from Assetto Corsa and write them to disk
        Configuration options can be found in src/config/record.yaml
    """

    def __init__(self):
        self.image_stream = ImageStream()
        self.state_capture = StateClient()
        self.__load_configuration()
        self.is_running = True
        self.frame_counter = 0

    def __load_configuration(self):
        self._config = load_yaml(RECORD_CONFIG_FILE)
        self.root_dir = self._config["save_path"]

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
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
        save_bytes(f"{self.root_dir}/{self.frame_counter}", state["state"])
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
