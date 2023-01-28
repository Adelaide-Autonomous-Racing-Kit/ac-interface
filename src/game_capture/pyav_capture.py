from concurrent.futures import ProcessPoolExecutor
from typing import Literal
import av
import cv2
import numpy as np
import platform
import yaml

from src.utils.os import sanitise_os_name, get_file_format, get_display_input
from src.utils.system_monitor import track_runtime, System_Monitor


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


def track_packet_creation_time(packet: av.Packet):
    creation_time = (time.time() - float(packet.pts * packet.time_base)) * 10e3
    System_Monitor.add_function_runtime("ffmpeg_capture", creation_time)


if __name__ == "__main__":
    with open("./src/config/game_capture.yaml") as file:
        game_capture_config = yaml.load(file, Loader=yaml.FullLoader)

    with open("./src/config/ffmpeg.yaml") as file:
        ffmpeg_config = yaml.load(file, Loader=yaml.FullLoader)

    os_name: Literal["windows", "darwin", "linux"] = sanitise_os_name(
        name=platform.system()
    )

    file_format: Literal["dshow", "avfoundation", "x11grab"] = get_file_format(
        os_name=os_name
    )

    file_input, video_size = get_display_input(
        os_name=os_name,
        game_name=game_capture_config.get("game_window_name"),
        game_resolution=game_capture_config.get("game_resolution"),
    )
    ffmpeg_config["video_size"] = video_size
    capture = av.open(file=file_input, format=file_format, options=ffmpeg_config)
    generator = capture.demux(capture.streams.video[0])
    executor = ProcessPoolExecutor(max_workers=2)
    import time

    i = 0
    for packet in generator:
        # track_packet_creation_time(packet)
        frame = get_frame(packet)
        display(frame)
        i += 1
        if i == 200:
            break

    System_Monitor.log_function_runtimes_times()
