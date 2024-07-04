from email.mime import image
from threading import Thread
import time
from typing import Dict

from aci.utils import display
from aci.utils.os import get_display_input, get_file_format, get_sanitised_os_name
from aci.utils.system_monitor import System_Monitor
import av
from loguru import logger
import numpy as np


def bgr0_to_bgr0(image: np.array) -> np.array:
    return image


def bgr0_to_bgr(image: np.array) -> np.array:
    return image[:, :, :3]


def bgr0_to_rgb(image: np.array) -> np.array:
    return bgr0_to_bgr(image)[:, :, ::-1]


IMAGE_FORMAT_CONVERSION = {
    "BGR0": bgr0_to_bgr0,
    "BGR": bgr0_to_bgr,
    "RGB": bgr0_to_rgb,
}


class ImageStream:
    """
    Captures and converts video from an application to an stream.
        Consumes frames from PyAV and converts them for use in inference
        or data recording. It continually refreshes the current image
        which can be access via the `latest_image` property
    """

    def __init__(self, config: Dict):
        self._latest_dts = -1
        self._is_new_frame = False
        self.__setup_configuration(config)
        self.__setup_frame_generator()
        self.__start_update_thread()

    @property
    def image(self) -> np.array:
        if self._wait_for_new_frames:
            self._wait_for_new_frame()
        self._is_new_frame = False
        return IMAGE_FORMAT_CONVERSION[self._image_format](self._latest_image)

    @property
    def is_stale(self) -> bool:
        return not self._is_new_frame

    def _wait_for_new_frame(self):
        """
        Blocking call that waits until a new image from the game is received
        """
        while not self._is_new_frame:
            pass

    def __setup_configuration(self, config: Dict):
        self._capture_config = config["images"]
        self._image_format = self._capture_config["image_format"]
        self._wait_for_new_frames = self._capture_config["wait_for_new_frames"]
        self._ffmpeg_config = config["ffmpeg"]
        self.__add_dynamic_configuration_options()

    def __add_dynamic_configuration_options(self):
        os_name = get_sanitised_os_name()
        self._file_format = get_file_format(os_name)
        self._file_input, video_size = get_display_input(
            os_name,
            game_name=self._capture_config.get("window_name"),
            game_resolution=self._capture_config.get("resolution"),
        )
        self._ffmpeg_config["video_size"] = video_size

    def __setup_frame_generator(self):
        capture_stream = av.open(
            file=self._file_input,
            format=self._file_format,
            options=self._ffmpeg_config,
        )
        self._frame_generator = capture_stream.decode()

    def __start_update_thread(self):
        """
        Starts a thread that consumes frames from by PyAV
        """
        self._is_running = True
        self.update_thread = Thread(target=self._run, daemon=True)
        self.update_thread.start()

    def _run(self):
        while self._is_running:
            frame = next(self._frame_generator)
            if not self._is_duplicate_frame(frame):
                bgr0_image = self._get_BGR0_image_from_frame(frame)
                self._latest_image = bgr0_image
                self._latest_dts = frame.dts
                self._is_new_frame = True

    def _is_duplicate_frame(self, frame) -> bool:
        return frame.dts == self._latest_dts

    def _get_BGR0_image_from_frame(self, frame: av.video.frame.VideoFrame) -> np.array:
        """
        Extract a BGR0 image from a stream frame as a numpy array
            Packet is a 24-bit 3 component BGR post-padded to 32-bits

        :frame: Stream frame to interpret.
        :type frame: av.video.frame.VideoFrame
        :return: Image as np.array in [h x w x c] in BGR channel order.
        :rtype: np.array
        """
        plane = frame.planes[0]
        from_buffer = np.frombuffer(plane, dtype=np.uint8)
        # Reshape to height x width  x 4
        return from_buffer.reshape(plane.height, plane.width, 4)

    def __repr__(self) -> str:
        resolution = self._capture_config["resolution"]
        framerate = self._ffmpeg_config["framerate"]
        encoder = self._ffmpeg_config["c:v"]
        to_print = "ImageStream\n"
        to_print += f"Target Window: {self._capture_config['window_name']}\n"
        to_print += f"Resolution: {resolution[0]}x{resolution[1]}\n"
        to_print += f"Framerate: {framerate}fps \n"
        to_print += f"Encoder: {encoder}\n"
        return to_print


# Small test loop to evaluate capture performance
def main():
    image_stream = ImageStream()
    display_sample_images(image_stream)
    bench_fps(image_stream)
    System_Monitor.log_function_runtimes_times()


def display_sample_images(image_stream):
    logger.info("Displaying sample images received")
    for _ in range(300):
        image = image_stream.latest_image
        display.image(image)


def bench_fps(image_stream):
    logger.info("Benchmarking frames per second throughput")
    start_time = time.time()
    n_frames = 900
    for _ in range(n_frames):
        _ = image_stream.latest_image
    elapsed_time = time.time() - start_time
    logger.info(
        f"Received {n_frames} frames in {elapsed_time}s {n_frames/elapsed_time}fps"
    )


def track_ffmpeg_capture_time(frame: av.video.frame.VideoFrame):
    """
    Adds an entry to system monitor for tracking the frame time of ffmpeg capture
        Make sure "use_wallclock_as_timestamps" is set to "1" in ffmpeg config
        before taking measurements, otherwise they may use a logical frame clock
    Note: Not 100% sure this captures what we think it does as it reports 300ms
        capture latency, but you are able to play the game in the opencv window,
        usually above 100ms is human perceivable for these sorts of games

    :packer: Stream packet to interpret.
    :type packet: av.Packet
    """
    creation_time = (time.time() - frame.time) * 10e3
    System_Monitor.add_function_runtime("ffmpeg_capture", creation_time)


if __name__ == "__main__":
    main()
