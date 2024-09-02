import ctypes
import multiprocessing as mp
from multiprocessing.shared_memory import SharedMemory
import signal
from typing import Dict

from aci.config.constants import CAPTURE_CONFIG_FILE
from aci.game_capture.video.pyav_capture import ImageStream
from aci.utils.ins import SimulatedINS
from aci.utils.load import load_yaml
from aci.utils.state import identity, process_state, simulate_ins_readings
from acs.client import StateClient
from acs.shared_memory.ac.combined import COMBINED_DATA_TYPES
import numpy as np


class GameCapture(mp.Process):
    """
    Process class that performs game capture in parallel to inference code
        Class can be instanced and capture started by calling game_capture.start()
        New captures can be received using game_capture.capture()
        To cleanly exit call game_capture.stop()
    """

    def __init__(self, config: Dict):
        super().__init__()
        self.__setup(config)

    @property
    def capture(self) -> Dict:
        """
        Blocking access that waits until a new image from the game is received before
            returning a capture dictionary

        :return: {Dictionary image: BGR image as np.array, state: bytes}
        :rtype: Dict[str : np.array, Union[bytes, Dict]]
        """
        image_mp_array, image_np_array = self._shared_image_buffer
        mp_buffer = self._shared_state_buffer
        self._wait_for_fresh_capture()
        with image_mp_array.get_lock():
            image = image_np_array.copy()
            state = mp_buffer.buf[:].tobytes()
        self.is_stale = True
        state = self._state_transform(state, self._simulated_INS)
        return {"state": state, "image": image}

    def _wait_for_fresh_capture(self):
        while self.is_stale:
            continue

    @capture.setter
    def capture(self, capture: Dict):
        """
        Accepts a capture dictionary and copies them to the shared memory buffer

        :capture: A Dictionary containing {"image": image, "state": state}
        :type capture: Dict[str : np.array, bytes]
        """
        image_mp_array, image_np_array = self._shared_image_buffer
        mp_buffer = self._shared_state_buffer
        with image_mp_array.get_lock():
            image_np_array[:] = capture["image"]
            mp_buffer.buf[:] = capture["state"]["state"]
        self.is_stale = False

    @property
    def state_bytes(self) -> bytes:
        """
        Access to game state bytes for database logging

        :return: state: raw game state bytes that can be decoded
        :rtype: bytes
        """
        image_mp_array, _ = self._shared_image_buffer
        mp_buffer = self._shared_state_buffer
        with image_mp_array.get_lock():
            state = mp_buffer.buf[:].tobytes()
        return state

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
        self.__setup_capture_process()
        while self.is_running:
            image = self.image_stream.image
            state = self.state_capture.latest_state
            self.capture = {"state": state, "image": image}

    def __setup_capture_process(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.image_stream = ImageStream(self._capture_config)
        self.state_capture = StateClient()

    def stop(self):
        """
        Stops the capture process
        """
        self.is_running = False
        self._shared_state_buffer.unlink()

    def __setup(self, config: Dict):
        self.__setup_configuration(config)
        self.__setup_processes_shared_memory()
        self.__setup_state_postprocessing()

    def __setup_configuration(self, config: dict):
        self._load_configuration(config)
        self._use_state_dicts = self._state_config["use_dicts"]
        self._simulate_ins = self._state_config["simulate_ins"]
        width, height = self._image_stream_config["resolution"]
        n_channels = 4 if self._image_stream_config["image_format"] == "BGR0" else 3
        self._image_shape = (height, width, n_channels)

    def __setup_state_postprocessing(self):
        self._simulated_INS = SimulatedINS()
        if self._simulate_ins:
            self._state_transform = simulate_ins_readings
        elif self._use_state_dicts:
            self._state_transform = process_state
        else:
            self._state_transform = identity

    def _load_configuration(self, config: Dict):
        self._capture_config = load_yaml(CAPTURE_CONFIG_FILE)
        if self._is_dynamic_config(config):
            self._override_default_configs(config["capture"])
        self._add_display_resolution(config)
        self._image_stream_config = self._capture_config["images"]
        self._state_config = self._capture_config["state"]

    def _is_dynamic_config(self, config: Dict) -> bool:
        return "capture" in config

    def _override_default_configs(self, config: Dict):
        if "images" in config:
            self._override_default_config(config, "images")
        if "state" in config:
            self._override_default_config(config, "state")
        if "ffmpeg" in config:
            self._override_default_config(config, "ffmpeg")

    def _override_default_config(self, config: Dict, config_name: str):
        self._capture_config[config_name].update(config[config_name])

    def _add_display_resolution(self, config: Dict):
        display_config = config["video.ini"]["VIDEO"]
        resolution = [int(display_config["WIDTH"]), int(display_config["HEIGHT"])]
        self._capture_config["images"]["resolution"] = resolution

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
        self._shared_state_buffer = SharedMemory(create=True, size=self.buffer_size)

    @property
    def buffer_size(self):
        return np.dtype(COMBINED_DATA_TYPES).itemsize

    def __setup_shared_flags(self):
        self._is_stale = mp.Value("i", True)
        self._is_running = mp.Value("i", True)
