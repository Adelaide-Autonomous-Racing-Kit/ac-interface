from src.game_capture.get_window import get_ACC_window_location_linux
from typing import Tuple

def sanitise_os_name(name: str) -> str:
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

def get_display_input(os_name: str, game_resolution: str) -> Tuple[str, str]:
    """
    Get the appropriate file input and video size for the given operating system.

    :param os_name: Operating system name, one of 'windows', 'darwin' or 'linux'.
    :type os_name: str
    :param game_resolution: A string containing width and height of the game we're trying to look for and capture i.e. 1920x1080
    :type game_resolution: str
    :returns: Tuple containing file input and video size
    :rtype: Tuple[str, str]
    :raises NotImplementedError: If the given operating system is not supported.
    """
    if os_name == "windows":
        raise NotImplementedError
    elif os_name == "darwin":
        raise NotImplementedError
    elif os_name == "linux":

        window_location = get_ACC_window_location_linux(game_resolution)

        file_input = f":0.0+{window_location[0]},{window_location[1]}"
        video_size = "x".join(map(str, game_resolution))
    else:
        raise NotImplementedError("Unsupported operating system")

    return file_input, video_size
