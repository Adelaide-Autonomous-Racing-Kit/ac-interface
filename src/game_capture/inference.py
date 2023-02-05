import multiprocessing as mp
import threading
import time
import ctypes
from typing import Dict, Tuple

import numpy as np
from loguru import logger

from src.game_capture.video.pyav_capture import ImageStream
from src.game_capture.state.client import StateClient
from src.game_capture.video.pyav_capture import display


class GameCapture(mp.Process):
    """
    Process class that performs game capture in parallel to inference code
    """

    def __init__(self):
        super().__init__()
        self.__setup_processes_shared_memory()

    @property
    def latest_capture(self) -> Dict:
        """
        Non-blocking call that returns the latest capture dictionary even if it is stale

        :return: Dictionary {image: BGR image as np.array, state: structured np.array}
        :rtype: Dict
        """
        self._wait_for_first_capture()
        return self._capture

    def _wait_for_first_capture(self):
        while self._capture is None:
            continue

    @property
    def fresh_capture(self) -> Dict[str, np.array]:
        """
        Blocking call that waits until a new image from the game is received before
            returning a capture dictionary

        :return: {Dictionary image: BGR image as np.array, state: structured np.array}
        :rtype: Dict[str : np.array]
        """
        self._wait_for_fresh_capture()
        return self._capture

    def _wait_for_fresh_capture(self):
        while self._is_stale:
            continue
        self._is_stale = True

    def _run(self):
        image_stream = ImageStream()
        # state_capture = StateClient()
        start_time = time.time()
        while self.is_running:
            image = image_stream.latest_image
            elapsed_time = time.time() - start_time
            logger.info(f"Frame received in: {elapsed_time*1E3}ms")
            # state = state_capture.latest_state
            self.image = image
            # self._capture = {"image": image, "state": state}
            start_time = time.time()

    @property
    def image(self) -> np.array:
        mp_array, np_array = self._shared_memory
        while self.is_stale:
            continue
        with mp_array.get_lock():
            image = np_array.copy()
        self.is_stale = True
        return image

    @image.setter
    def image(self, image: np.array):
        mp_array, np_array = self._shared_memory
        with mp_array.get_lock():
            np_array[:] = image
        self.is_stale = False

    @property
    def is_stale(self) -> bool:
        with self._is_stale.get_lock():
            is_stale = self._is_stale.value
        return is_stale

    @is_stale.setter
    def is_stale(self, is_stale: bool):
        with self._is_stale.get_lock():
            self._is_stale.value = is_stale

    @property
    def is_running(self) -> bool:
        with self._is_running.get_lock():
            is_running = self._is_running.value
        return is_running

    @is_running.setter
    def is_running(self, is_running: bool):
        with self._is_running.get_lock():
            self._is_running.value = is_running

    def run(self):
        """
        Called on Proccess.start()
        """
        image_stream = ImageStream()
        # state_capture = StateClient()
        start_time = time.time()
        while self.is_running:
            image = image_stream.latest_image
            # state = state_capture.latest_state
            self.image = image
            # self._capture = {"image": image, "state": state}

    def stop(self):
        """
        Stops the capture process and its update thread
        """
        self.is_running = False

    def __setup_processes_shared_memory(self):
        image_shape = (768, 1024, 3)  # TODO: Load this from game_capture.yaml
        n_pixels = image_shape[0] * image_shape[1] * image_shape[2]
        mp_array = mp.Array(ctypes.c_uint8, n_pixels)
        np_array = np.ndarray(image_shape, dtype=np.uint8, buffer=mp_array.get_obj())
        self._shared_memory = (mp_array, np_array)
        self._is_stale = mp.Value("i", True)
        self._is_running = mp.Value("i", True)


def main():
    n_captures = 300
    game_capture = GameCapture()
    game_capture.start()
    logger.info("Started Capture Process")
    # Wait until first image has been received
    _ = game_capture.image
    start_time = time.time()
    for _ in range(n_captures):
        image = game_capture.image
        display(image)
    elapsed_time = time.time() - start_time
    game_capture.stop()
    logger.info(f"Read {n_captures} in {elapsed_time}s {n_captures/elapsed_time}Hz")


if __name__ == "__main__":
    main()
