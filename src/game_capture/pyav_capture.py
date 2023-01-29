from concurrent.futures import ProcessPoolExecutor
from typing import Literal
import av
import cv2
import numpy as np
import yaml

from src.utils.os import get_sanitised_os_name, get_file_format, get_display_input
from src.utils.system_monitor import track_runtime, System_Monitor
from src.utils.load import load_yaml


def save_frame(frame, i):
    np.save(f"./test/{i}", frame)


@track_runtime
def display(frame):
    cv2.imshow("OpenCV capture", frame)
    cv2.waitKey(1)


@track_runtime
def get_frame(packet: av.Packet) -> np.array:
    """
    Extract a video frame from a stream packet as a numpy array
        Packet is a 24-bit 3 component BGR post-padded to 32-bits

    :packer: Stream packet to interpret.
    :type packet: av.Packet
    :return: Frame as np.array in [h x w x c] in BGR channel order.
    :rtype: np.array
    """
    plane = packet.decode()[0].planes[0]
    from_buffer = np.frombuffer(plane, dtype=np.uint8)
    # Reshape to height x width  x 4 and slice off padded zeros in 4th channel
    return from_buffer.reshape(plane.height, plane.width, 4)[:, :, :3]


def track_ffmpeg_capture_time(packet: av.Packet):
    """
    Adds an entry to system monitor for tracking the frame time of ffmpeg capture
        Make sure "use_wallclock_as_timestamps" is set to "1" in ffmpeg config
        before taking measurements, otherwise they may use a logical frame clock

    :packer: Stream packet to interpret.
    :type packet: av.Packet
    """
    creation_time = (time.time() - float(packet.pts * packet.time_base)) * 10e3
    System_Monitor.add_function_runtime("ffmpeg_capture", creation_time)


class FrameCapture:
    def __init__(self) -> None:
        self._load_configurations()
        self._setup_capture_stream()
        self._setup_frame_generator()

    def _load_configurations(self):
        self._game_capture_config = load_yaml("./src/config/game_capture.yaml")
        self._ffmpeg_config = load_yaml("./src/config/ffmpeg.yaml")
        self._add_dynamic_configuration_options()

    def _add_dynamic_configuration_options(self):
        os_name = get_sanitised_os_name()
        self._file_format = get_file_format(os_name)
        self._file_input, video_size = get_display_input(
            os_name,
            game_name=self._game_capture_config.get("game_window_name"),
            game_resolution=self._game_capture_config.get("game_resolution"),
        )
        self._ffmpeg_config["video_size"] = video_size

    def _setup_capture_stream(self):
        self._capture_stream = av.open(
            file=self._file_input,
            format=self._file_format,
            options=self._ffmpeg_config,
        )

    def _setup_frame_generator(self):
        capture_stream = self._capture_stream
        self._frame_generator = capture_stream.demux(capture_stream.streams.video[0])


if __name__ == "__main__":
    frame_capture = FrameCapture()

    i = 0
    for packet in frame_capture._frame_generator:
        # track_ffmpeg_capture_time(packet)
        frame = get_frame(packet)
        display(frame)
        i += 1
        if i == 200:
            break

    System_Monitor.log_function_runtimes_times()
