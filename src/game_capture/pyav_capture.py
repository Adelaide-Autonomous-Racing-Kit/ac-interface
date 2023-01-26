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
def decode_packet(packet):
    return packet.decode()[0]


@track_runtime
def convert_to_rgb(frame):
    return frame.to_rgb()


@track_runtime
def convert_to_ndarray(frame):
    return frame.to_ndarray()


@track_runtime
def convert_from_brg(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


@track_runtime
def display(frame):
    cv2.imshow("OpenCV capture", frame)
    cv2.waitKey(1)


@track_runtime
def get_frame(packet):
    frame = decode_packet(packet)
    frame = convert_to_rgb(frame)
    frame = convert_to_ndarray(frame)
    frame = convert_from_brg(frame)
    executor.submit(save_frame, frame, i)
    return frame


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

    i = 0
    for packet in generator:
        frame = get_frame(packet)
        display(frame)
        i += 1
        if i == 200:
            break

    System_Monitor.log_function_runtimes_times()
