import cv2
from pathlib import Path

import numpy as np


def rgb_to_bgr(image: np.array) -> np.array:
    return image[:, :, ::-1]


def noramlise_values(values: np.array) -> np.array:
    values -= values.min()
    values /= values.ptp()


def reverse_sign_of_values(values: np.array):
    values -= 1
    values *= -1


def convert_to_uint8(values) -> np.array:
    values *= 255
    values.astype(np.uint8, copy=False)


def allocate_empty_frame(
    width: int,
    height: int,
    channels: int = 0,
) -> np.array:
    shape = (width, height)
    if channels > 0:
        shape = (*shape, channels)
    return np.zeros(shape, dtype=np.uint8)


def save_image(to_save: np.array, filepath: Path, flipud: bool):
    to_save = np.rot90(to_save)
    if flipud:
        to_save = np.flipud(to_save)
    cv2.imwrite(str(filepath), to_save)
