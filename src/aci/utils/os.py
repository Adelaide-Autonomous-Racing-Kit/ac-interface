import os
import platform
from typing import List, Tuple

from Xlib.display import Display
from aci.config.constants import GAME_NAME_TO_WINDOW_NAME
from aci.game_capture.video.get_window import (
    get_window_linux,
    get_window_location_linux,
)
from aci.utils.data import Point
from pywinctl import Window


def get_sanitised_os_name() -> str:
    name = platform.system()
    if name is None or name.strip() == "":
        raise ValueError("os_name cannot be None or an empty string")
    name = name.lower()
    return name


def get_file_format(os_name: str) -> str:
    """
    Get the file format for capturing video based on the operating system.

    :param os_name: The name of the operating system.
    :type os_name: str
    :return: The file format for the given operating system.
    :rtype: str
    :raise NotImplementedError: If the operating system is not supported.
    """
    if os_name == "windows":
        return "dshow"
    elif os_name == "darwin":
        return "avfoundation"
    elif os_name == "linux":
        return "x11grab"
    else:
        raise NotImplementedError("Unsupported operating system")


def get_display_input(
    os_name: str, game_name: str, game_resolution: List[int]
) -> Tuple[str, str]:
    """
    Get the appropriate file input and video size for the given operating system.

    :param os_name: Operating system name, one of 'windows', 'darwin' or 'linux'.
    :type os_name: str
    :param game_name: Name of the game
    :type game_name: str
    :param game_resolution: A list containing width and height of the game we're trying to look for and capture i.e. [1600, 900]
    :type game_resolution: List[int]
    :returns: Tuple containing file input and video size
    :rtype: Tuple[str, str]
    :raises NotImplementedError: If the given operating system is not supported.
    """
    window_name = GAME_NAME_TO_WINDOW_NAME[os_name][game_name]
    if os_name == "windows":
        raise NotImplementedError
    elif os_name == "darwin":
        raise NotImplementedError
    elif os_name == "linux":
        window_location = get_window_location_linux(window_name, game_resolution)
        file_input = (
            f"{os.environ['DISPLAY']}.0+{window_location.x},{window_location.y}"
        )
        video_size = "x".join(map(str, game_resolution))
    else:
        raise NotImplementedError("Unsupported operating system")

    return file_input, video_size


def get_application_window_coordinates(
    game_name: str, game_resolution: List[int]
) -> Point:
    """
    Get the coordinates of the top-left corner of the application's window

    :param game_name: Name of the game
    :type game_name: str
    :param game_resolution: A list containing width and height of the game we're trying to look for and capture i.e. [1600, 900]
    :type game_resolution: List[int]
    :returns: Point object containing the x,y location of the top-left of the application's window
    :rtype: Point
    """
    os_name = get_sanitised_os_name()
    window_name = GAME_NAME_TO_WINDOW_NAME[os_name][game_name]
    return get_window_location_linux(window_name, game_resolution)


def move_application_window(
    game_name: str,
    game_resolution: List[int],
    location: Point,
):
    """
    Get the coordinates of the top-left corner of the application's window

    :param game_name: Name of the game
    :type game_name: str
    :param game_resolution: A list containing width and height of the game we're trying to look for and capture i.e. [1600, 900]
    :type game_resolution: List[int]
    :param location: Point object containing the x,y desired location of the top-left of the application's window
    :type Point
    """
    os_name = get_sanitised_os_name()
    window_name = GAME_NAME_TO_WINDOW_NAME[os_name][game_name]
    xwindow = get_window_linux(window_name, game_resolution)
    window = Window(xwindow)
    window.moveTo(location.x, location.y)
    window.alwaysOnTop(True)


def get_default_window_location(window_resolution: List[int]) -> Point:
    """
    Get the coordinates for the application window such that it is in the top right corner of the monitor

    :param game_resolution: A list containing width and height of the application window
    :type game_resolution: List[int]
    :param location: Point object containing the x,y desired location of the top-left of the application's window
    :type Point
    """
    display = Display()
    width = display.screen().width_in_pixels
    x_position = width - window_resolution[0]
    return Point(x=x_position, y=0)
