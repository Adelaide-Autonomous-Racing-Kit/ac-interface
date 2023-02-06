from subprocess import Popen, PIPE
import numpy as np

from src.game_capture.video.pyav_capture import display
from src.utils.os import get_display_input, get_sanitised_os_name
from src.utils.load import load_yaml

if __name__ == "__main__":
    game_capture_config = load_yaml("./src/config/game_capture.yaml")
    os_name = get_sanitised_os_name()

    file_input, video_size = get_display_input(
        os_name,
        game_name=game_capture_config.get("game_window_name"),
        game_resolution=game_capture_config.get("game_resolution"),
    )
    p1 = Popen(
        [
            "ffmpeg",
            "-f",
            "x11grab",
            "-vcodec",
            "rawvideo",
            "-r",
            "60",
            "-s",
            video_size,
            "-i",
            file_input,
            "-f",
            "rawvideo",
            "-c:v",
            "copy",
            "pipe:",
        ],
        stdout=PIPE,
    )
    p2 = Popen(
        [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            "1920x1080",
            "-i",
            "-",
            "-vcodec",
            "h264_nvenc",
            "-r",
            "60",
            "video.mp4",
        ],
        stdin=PIPE,
    )
    while True:
        # Read width*height*3 bytes from stdout (1 frame)
        raw_frame = p1.stdout.read(1920 * 1080 * 4)
        if raw_frame is None:
            print("hit")
        p2.stdin.write(raw_frame)
        # display(frame)
