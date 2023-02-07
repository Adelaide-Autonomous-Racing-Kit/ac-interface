import ctypes
import multiprocessing as mp
import time
from typing import Dict

import numpy as np
from loguru import logger

from src.game_capture.video.pyav_capture import ImageStream
from src.game_capture.state.client import StateClient
from src.game_capture.video.pyav_capture import display
from src.game_capture.state.shared_memory import SHMStruct
from src.utils.load import load_yaml, state_array_to_dict


class GameCapture(mp.Process):
    """
    Process class that performs game capture in parallel to inference code
        Class can be instanced and capture started by calling game_capture.start()
        New captures can be received using game_capture.capture()
        To cleanly exit call game_capture.stop()
    """

    def __init__(self):
        super().__init__()
        self.__setup_configuration()
        self.__setup_processes_shared_memory()

    @property
    def capture(self) -> np.array:
        """
        Blocking access that waits until a new image from the game is received before
            returning a capture dictionary

        :return: {Dictionary image: BGR image as np.array, state: Dict{str: float}}
        :rtype: Dict[str : np.array]
        """
        image_mp_array, image_np_array = self._shared_image_buffer
        _, state_np_array = self._shared_state_buffer
        self._wait_for_fresh_capture()
        with image_mp_array.get_lock():
            image = image_np_array.copy()
            state = state_np_array.copy()
        self.is_stale = True
        return {"image": image, "state": state_array_to_dict(state)}

    def _wait_for_fresh_capture(self):
        while self.is_stale:
            continue

    @capture.setter
    def capture(self, capture: Dict[str, np.array]):
        """
        Accepts a capture dictionary and copies them to the shared memory buffer

        :capture: A Dictionary containing {"image": image, "state": state}
        :type capture: Dict[str : np.array]
        """
        image_mp_array, image_np_array = self._shared_image_buffer
        _, state_np_array = self._shared_state_buffer
        with image_mp_array.get_lock():
            image_np_array[:] = capture["image"]
            state_np_array[:] = np.asarray(capture["state"].tolist())
        self.is_stale = False

    @property
    def is_stale(self) -> bool:
        """
        Checks if the current capture has been read by any consumer

        :return: True if the capture has been read, false if it has not
        :rtype: bool
        """
        with self._is_stale.get_lock():
            is_stale = self._is_stale.value
        return is_stale

    @is_stale.setter
    def is_stale(self, is_stale: bool):
        """
        Sets the flag indicating if the capture has been read previously

        :is_stale: True if the capture has been read, false if it has not
        :type is_stale: bool
        """
        with self._is_stale.get_lock():
            self._is_stale.value = is_stale

    @property
    def is_running(self) -> bool:
        """
        Checks if the capture process is running

        :return: True if the capture process is running, false if it is not
        :rtype: bool
        """
        with self._is_running.get_lock():
            is_running = self._is_running.value
        return is_running

    @is_running.setter
    def is_running(self, is_running: bool):
        """
        Sets if the capture process is running

        :is_running: True if the capture process is running, false if it is not
        :type is_running: bool
        """
        with self._is_running.get_lock():
            self._is_running.value = is_running

    def run(self):
        """
        Called on GameCapture.start()
        """
        image_stream = ImageStream()
        state_capture = StateClient()
        while self.is_running:
            image = image_stream.latest_image
            state = state_capture.latest_state
            self.capture = {"image": image, "state": state}

    def stop(self):
        """
        Stops the capture process
        """
        self.is_running = False

    def __setup_configuration(self):
        width, height = load_yaml("./src/config/game_capture.yaml")["game_resolution"]
        self._image_shape = (height, width, 3)

    def __setup_processes_shared_memory(self):
        self.__setup_shared_image_buffer()
        self.__setup_shared_state_buffer()
        self.__setup_shared_flags()

    def __setup_shared_image_buffer(self):
        mp_array = mp.Array(ctypes.c_uint8, self._n_pixels)
        np_array = np.ndarray(
            self._image_shape, dtype=np.uint8, buffer=mp_array.get_obj()
        )
        self._shared_image_buffer = (mp_array, np_array)

    @property
    def _n_pixels(self):
        return int(np.prod(self._image_shape))

    def __setup_shared_state_buffer(self):
        mp_array = mp.RawArray("f", self._n_state_fields)
        np_array = np.ndarray(self._n_state_fields, dtype="f", buffer=mp_array)
        self._shared_state_buffer = (mp_array, np_array)

    @property
    def _n_state_fields(self):
        return len(SHMStruct._fields_)

    def __setup_shared_flags(self):
        self._is_stale = mp.Value("i", True)
        self._is_running = mp.Value("i", True)


def main():
    benchmark_interprocess_communication()


def benchmark_interprocess_communication():
    n_captures = 900
    logger.info(f"Benchmarking game capture reading from capture process")
    game_capture = GameCapture()
    game_capture.start()
    # Wait until first image has been received
    _ = game_capture.capture
    start_time = time.time()
    for _ in range(n_captures):
        _ = game_capture.capture
    elapsed_time = time.time() - start_time
    game_capture.stop()
    logger.info(f"Read {n_captures} in {elapsed_time}s {n_captures/elapsed_time}Hz")


if __name__ == "__main__":
    main()
