import time
from typing import List, Set, Union

from Xlib.display import Display
from aci.utils.data import Point

N_MAX_RETRIES = 5


class WindowNotFoundError(Exception):
    pass


def get_window_location_linux(names: Set[str], resolution: List[int]) -> Point:
    """
    This function is used to get the location of a specific window with the given name on a Linux system.

    :param name: The name of the window you are trying to find.
    :type name: str
    :param resolution: The resolution of the window.
    :type resolution: List[int]
    :return: A tuple of integers representing the x and y coordinates of the top-left corner of the window.
    :rtype: List[int]
    """
    window = get_window_linux(names, resolution)
    return get_window_absolute_location(window)


def get_window_linux(names: Set[str], resolution: List[int]) -> Display:
    """
    This function is used to get the location of a specific window with the given name on a Linux system.

    :param name: The name of the window you are trying to find.
    :type name: str
    :param resolution: The resolution of the window.
    :type resolution: List[int]
    :return: A tuple of integers representing the x and y coordinates of the top-left corner of the window.
    :rtype: List[int]
    """
    display = Display()
    root = display.screen().root
    window, n_retries = None, 0
    while window is None:
        window = get_window_linux_recurse(root, names, resolution)
        if window is None:
            if n_retries == N_MAX_RETRIES:
                raise WindowNotFoundError(
                    f"Unable to find a window named {names} with resolution {resolution[0]}x{resolution[1]}"
                )
            n_retries += 1
            time.sleep(0.5)
    return window


def get_window_linux_recurse(
    window: Display, names: Set[str], resolution: List[int]
) -> Union[Display, None]:
    """
    This function recurses the active displays finding the location of a specific window with a given name on a Linux system.

    :param window: The current window.
    :type window: Xlib.Display
    :param name: The name of the window you are trying to find.
    :type name: str
    :param resolution: The resolution of the window you are trying to find.
    :type resolution: List[int]
    :return: A Point representing the x and y coordinates of the top-left corner of the window if found. None otherwise.
    :rtype: Point or None
    """
    children = window.query_tree().children
    for w in children:
        if w.get_wm_class():
            if is_named_match(w, names) and is_correct_resolution(w, resolution):
                return w
        w = get_window_linux_recurse(w, names, resolution)
        if w is not None:
            return w
    return None


def is_named_match(window: Display, names: Set[str]) -> bool:
    """
    Check if the window has the given name.

    :param window: The window to check
    :type window: Display
    :param name: The name to check against
    :type name: str
    :return: True if the window has the given name, False otherwise
    :rtype: bool
    """
    return window.get_wm_class()[0] in names


def is_correct_resolution(window: Display, resolution: List[int]) -> bool:
    """
    Check if the window has the correct resolution.

    :param window: The window to check
    :type window: Display
    :param resolution: The resolution to check against
    :type resolution: List[int]
    :return: True if the window has the correct resolution, False otherwise
    :rtype: bool
    """
    geometry = window.get_geometry()
    is_same_height = resolution[1] == geometry.height
    is_same_width = resolution[0] == geometry.width
    return is_same_height and is_same_width


def get_window_absolute_location(window: Display) -> Point:
    """
    Get the absolute location of the window.

    :param window: The window to get the location of
    :type window: Display
    :return: A Point representing the x and y coordinates of the top-left corner of the window
    :rtype: Point
    """
    location = get_window_location(window)
    parent_window = window.query_tree().parent
    if not (parent_window == 0):
        sub_window_location = get_window_absolute_location(parent_window)
        location += sub_window_location
    return location


def get_window_location(window: Display) -> Point:
    """
    Get the location of the window.

    :param window: The window to get the location of
    :type window: Display
    :return: A Point representing the x and y coordinates of the top-left corner of the window
    :rtype: Point
    """
    geometry = window.get_geometry()
    return Point(geometry.x, geometry.y)
