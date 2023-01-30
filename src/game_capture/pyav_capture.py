import threading
import time
import av
import cv2
import numpy as np

from src.utils.os import get_sanitised_os_name, get_file_format, get_display_input
from src.utils.system_monitor import track_runtime, System_Monitor
from src.utils.load import load_yaml


class ImageStream:
    """
    Captures and converts video from an application to an stream.
    Is a generator that yields images as numpy arrays.
    """

    def __init__(self) -> None:
        self.__load_configurations()
        self.__setup_frame_generator()

    def __load_configurations(self):
        self._game_capture_config = load_yaml("./src/config/game_capture.yaml")
        self._ffmpeg_config = load_yaml("./src/config/ffmpeg.yaml")
        self.__add_dynamic_configuration_options()

    def __add_dynamic_configuration_options(self):
        os_name = get_sanitised_os_name()
        self._file_format = get_file_format(os_name)
        self._file_input, video_size = get_display_input(
            os_name,
            game_name=self._game_capture_config.get("game_window_name"),
            game_resolution=self._game_capture_config.get("game_resolution"),
        )
        self._ffmpeg_config["video_size"] = video_size

    def __setup_frame_generator(self):
        capture_stream = av.open(
            file=self._file_input,
            format=self._file_format,
            options=self._ffmpeg_config,
        )
        self._frame_generator = capture_stream.decode()

    @track_runtime
    def _get_image_from_frame(self, frame: av.video.frame.VideoFrame) -> np.array:
        """
        Extract an image from a stream frame as a numpy array
            Packet is a 24-bit 3 component BGR post-padded to 32-bits

        :packer: Stream frame to interpret.
        :type packet: av.video.frame.VideoFrame
        :return: Image as np.array in [h x w x c] in BGR channel order.
        :rtype: np.array
        """
        plane = frame.planes[0]
        from_buffer = np.frombuffer(plane, dtype=np.uint8)
        # Reshape to height x width  x 4 and slice off padded zeros in 4th channel
        return from_buffer.reshape(plane.height, plane.width, 4)[:, :, :3]

    def __iter__(self) -> np.array:
        """
        Generator definition that consumes from PyAVs frame stream and converts
            frames into image in the form of np.arrays

        :return: Images as np.array in [h x w x c] in BGR channel order.
        :rtype: np.array
        """
        while True:
            frame = next(self._frame_generator)
            # track_ffmpeg_capture_time(frame)
            image = self._get_image_from_frame(frame)
            yield image

    def __repr__(self) -> str:
        resolution = self._game_capture_config["game_resolution"]
        framerate = self._ffmpeg_config["framerate"]
        encoder = self._ffmpeg_config["c:v"]
        to_print = "ImageStream\n"
        to_print += f"Target Window: {self._game_capture_config['game_window_name']}\n"
        to_print += f"Resolution: {resolution[0]}x{resolution[1]}\n"
        to_print += f"Framerate: {framerate}fps \n"
        to_print += f"Encoder: {encoder}\n"
        return to_print


def display(image: np.array):
    cv2.imshow("OpenCV capture", image)
    cv2.waitKey(1)


def track_ffmpeg_capture_time(frame: av.video.frame.VideoFrame):
    """
    Adds an entry to system monitor for tracking the frame time of ffmpeg capture
        Make sure "use_wallclock_as_timestamps" is set to "1" in ffmpeg config
        before taking measurements, otherwise they may use a logical frame clock

    :packer: Stream packet to interpret.
    :type packet: av.Packet
    """
    creation_time = (time.time() - frame.time) * 10e3
    System_Monitor.add_function_runtime("ffmpeg_capture", creation_time)


# Small test loop to evaluate capture performance
if __name__ == "__main__":
    image_stream = ImageStream()
    i = 0
    for image in image_stream:
        display(image)
        i += 1
        if i == 300:
            break

    System_Monitor.log_function_runtimes_times()
