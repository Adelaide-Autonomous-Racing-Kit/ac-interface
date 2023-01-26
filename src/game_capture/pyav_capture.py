from typing import Tuple, Literal
import glob
import av
import cv2
import numpy as np
import platform
import yaml

from src.utils.os import sanitise_os_name, get_file_format, get_display_input


if __name__ == "__main__":
    with open(glob.glob("**/game_capture.yaml")[0]) as file:
        game_capture_config = yaml.load(file, Loader=yaml.FullLoader)

    with open(glob.glob("**/ffmpeg.yaml")[0]) as file:
        ffmpeg_config = yaml.load(file, Loader=yaml.FullLoader)

    os_name: Literal["windows", "darwin", "linux"] = sanitise_os_name(
        name=platform.system()
    )

    file_format: Literal["dshow", "avfoundation", "x11grab"] = get_file_format(
        os_name=os_name
    )

    file_input, video_size = get_display_input(
        os_name=os_name, game_resolution=game_capture_config.get("game_resolution")
    )
    ffmpeg_config["video_size"] = video_size

    capture = av.open(file=file_input, format=file_format, options=ffmpeg_config)
    generator = capture.demux(capture.streams.video[0])
    for packet in generator:
        frame = np.asarray(packet.decode()[0].to_image())
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.imshow("OpenCV capture", frame)
        cv2.waitKey(1)
    print("Done")
