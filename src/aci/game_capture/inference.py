from contextlib import contextmanager
import ctypes
import multiprocessing as mp
from multiprocessing.shared_memory import SharedMemory
import select
import signal
import socket
import time
from typing import Dict

from aci.config.constants import CAPTURE_CONFIG_FILE
from aci.game_capture.video.game_frame import FrameCaptureError
from aci.game_capture.video.source import open_image_source
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
        while True:
            self._wait_for_fresh_capture()
            with self._capture_lock():
                if self.is_stale:
                    continue
                self.is_stale = True
                is_image_stale = self.is_image_stale
                if not is_image_stale:
                    self._image = self._shared_image_buffer[1].copy()
                    self.is_image_stale = True
                    if self._direct:
                        self._metadata = dict(
                            zip(self._metadata_fields, self._frame_meta)
                        )
                        self._metadata["capture_drops"] = (
                            self._metadata["frame_id"]
                            - self._last_read_frame
                            - 1
                            - (self._metadata["source_drops"] - self._last_source_drops)
                        ) + self._capture_drops
                        self._capture_drops = self._metadata["capture_drops"]
                        self._last_read_frame = self._metadata["frame_id"]
                        self._last_source_drops = self._metadata["source_drops"]
                state = self._shared_state_buffer.buf[:].tobytes()
                break
        result = {
            "state": self._state_transform(state, self._simulated_INS),
            "image": self._image,
            "is_image_stale": is_image_stale,
        }
        if self._direct:
            result["image_metadata"] = self._metadata.copy()
        return result

    def _wait_for_fresh_capture(self):
        while True:
            if not self.is_running:
                raise FrameCaptureError("Game capture stopped")
            if self._error_receive.poll():
                try:
                    message = self._error_receive.recv()
                except EOFError:
                    message = "Game capture stopped"
                raise FrameCaptureError(message)
            if self.pid is not None and not self.is_alive():
                raise FrameCaptureError(
                    f"Game capture stopped (exit code {self.exitcode})"
                )
            if not self.is_stale:
                return
            ready, _, _ = select.select([self._notify_read], [], [], 0.1)
            if ready:
                try:
                    self._notify_read.recv(1)
                except BlockingIOError:
                    pass

    @capture.setter
    def capture(self, capture: Dict):
        """Publish a complete image (if any) and the latest independent state."""
        notify = False
        with self._capture_lock():
            image = capture["image"]
            if image is not None:
                self._shared_image_buffer[1][:] = image
                if self._direct:
                    metadata = capture["image_metadata"]
                    self._frame_meta[:] = [
                        metadata[key] for key in self._metadata_fields
                    ]
                self.is_image_stale = False
                self._has_frame.value = True
            self._update_state(capture["state"])
            if self._has_frame.value and (
                image is not None or not self._wait_for_frames
            ):
                notify = self.is_stale
                self.is_stale = False
        if notify:
            try:
                self._notify_write.send(b"F")
            except BlockingIOError:
                pass  # A notification is already queued.

    @contextmanager
    def _capture_lock(self):
        lock = self._shared_image_buffer[0].get_lock()
        if not lock.acquire(timeout=0.5):
            raise FrameCaptureError("Game capture shared buffer stopped responding")
        try:
            yield
        finally:
            lock.release()

    def _update_state(self, state: Dict):
        mp_buffer = self._shared_state_buffer
        mp_buffer.buf[:] = state["state"]

    @property
    def state_bytes(self) -> bytes:
        """
        Access to game state bytes for database logging

        :return: state: raw game state bytes that can be decoded
        :rtype: bytes
        """
        mp_buffer = self._shared_state_buffer
        with self._capture_lock():
            state = mp_buffer.buf[:].tobytes()
        return state

    @property
    def is_stale(self):
        return self._is_stale.value

    @is_stale.setter
    def is_stale(self, value):
        self._is_stale.value = value

    @property
    def is_image_stale(self):
        return self._is_image_stale.value

    @is_image_stale.setter
    def is_image_stale(self, value):
        self._is_image_stale.value = value

    @property
    def is_running(self):
        return self._is_running.value

    @is_running.setter
    def is_running(self, value):
        self._is_running.value = value

    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self._error_receive.close()
        self._notify_read.close()
        image_stream = state_capture = None
        try:
            image_stream = open_image_source(self._capture_config)
            state_capture = StateClient()
            while self.is_running:
                frame = image_stream.read_latest()
                # StateClient.latest_state spins while waiting for the first packet.
                # Direct capture must still service its socket during that interval.
                if self._direct:
                    state = state_capture._latest_state
                    if not state_capture.update_thread.is_alive():
                        raise FrameCaptureError("Game state stream disconnected")
                else:
                    state = state_capture.latest_state
                if state is not None:
                    image, metadata = frame if frame is not None else (None, None)
                    self.capture = {
                        "state": state,
                        "image": image,
                        "image_metadata": metadata,
                    }
                time.sleep(0.001)
        except FrameCaptureError as error:
            self._error_send.send(str(error)[:2048])
            raise SystemExit(1) from None
        except Exception as error:
            self._error_send.send(str(error)[:2048])
            raise
        finally:
            if state_capture is not None:
                state_capture.stop()
            if image_stream is not None:
                image_stream.close()
            self._shared_state_buffer.close()
            self._error_send.close()
            self._notify_write.close()

    def stop(self):
        """Stop the capture process and release its shared state."""
        if self._resources_closed:
            return
        self._resources_closed = True
        self.is_running = False
        if self.pid is not None:
            self.join(timeout=2)
            if self.is_alive():
                self.terminate()
                self.join(timeout=2)
                if self.is_alive():
                    self.kill()
                    self.join(timeout=2)
        self._error_receive.close()
        self._error_send.close()
        self._notify_read.close()
        self._notify_write.close()
        try:
            self._shared_state_buffer.unlink()
        except FileNotFoundError:
            pass
        self._shared_state_buffer.close()

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
        self._image = None
        self._metadata = {}
        self._resources_closed = False
        self._metadata_fields = (
            "frame_id",
            "present_hook_ns",
            "received_ns",
            "source_drops",
        )
        self._capture_drops = self._last_read_frame = self._last_source_drops = 0
        self._direct = self._image_stream_config["backend"] == "game_frame"
        self._wait_for_frames = (
            self._direct and self._image_stream_config["wait_for_new_frames"]
        )

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
        self._is_stale = mp.RawValue("b", True)
        self._is_image_stale = mp.RawValue("b", True)
        self._has_frame = mp.RawValue("b", False)
        self._frame_meta = mp.RawArray("Q", len(self._metadata_fields))
        self._notify_read, self._notify_write = socket.socketpair(
            type=socket.SOCK_DGRAM
        )
        self._notify_read.setblocking(False)
        self._notify_write.setblocking(False)
        self._error_receive, self._error_send = mp.Pipe(duplex=False)
        self._is_running = mp.RawValue("b", True)
