from dataclasses import dataclass
from typing import List, Union

from Xlib.display import Display


@dataclass
class Point:
    """
    A class representing a point in 2D space
    """

    x: int
    y: int

    def __add__(self, point):
        x = self.x + point.x
        y = self.y + point.y
        return Point(x, y)

    def __repr__(self) -> str:
        return f"(x={self.x}, y={self.y})"


class WindowNotFoundError(Exception):
    pass


def get_window_location_linux(name: str, resolution: List[int]) -> List[int]:
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
    location = get_window_location_linux_recurse(root, name, resolution)
    if location is None:
        raise WindowNotFoundError(
            f"Unable to find a window named {name} with resolution {resolution[0]}x{resolution[1]}"
        )
    return location


def get_window_location_linux_recurse(
    window: Display, name: str, resolution: List[int]
) -> Union[Point, None]:
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
            if is_named_match(w, name) and is_correct_resolution(w, resolution):
                return get_window_absolute_location(w)
        window_location = get_window_location_linux_recurse(w, name, resolution)
        if window_location is not None:
            return window_location
    return None


def is_named_match(window: Display, name: str) -> bool:
    """
    Check if the window has the given name.

    :param window: The window to check
    :type window: Display
    :param name: The name to check against
    :type name: str
    :return: True if the window has the given name, False otherwise
    :rtype: bool
    """
    return window.get_wm_class()[0] == name


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
