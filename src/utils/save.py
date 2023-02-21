from pathlib import Path

import numpy as np
from turbojpeg import TJPF_BGRX, TurboJPEG

TURBO_JPEG = TurboJPEG()


def save_bgr0_as_jpeg(filepath: str, image: np.array):
    """
    Encodes BGR0 pixel format images as JPEGs and saves them to file
    """
    with open(f"{filepath}.jpeg", "wb") as file:
        image = TURBO_JPEG.encode(image, pixel_format=TJPF_BGRX)
        file.write(image)


def save_bytes(filepath: str, state_bytes: bytes):
    with open(f"{filepath}.bin", "wb") as file:
        file.write(state_bytes)


def maybe_create_folders(path: str):
    """
    If the folders in the path doesn't exist, create them

    :path: Folder path required to exist
    :type path: str
    """
    path = Path(path)
    if path.exists():
        return
    path.mkdir(parents=True)
