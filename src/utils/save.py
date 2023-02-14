from pathlib import Path

import numpy as np
from turbojpeg import TurboJPEG, TJPF_BGRX

TURBO_JPEG = TurboJPEG()


def save_bgr0_as_jpeg(filepath: str, image: np.array):
    """
    Encodes BGR0 pixel format images as JPEGs and saves them to file
    """
    with open(f"{filepath}.jpeg", "wb") as file:
        image = TURBO_JPEG.encode(image, pixel_format=TJPF_BGRX)
        file.write(image)


def save_state(filepath: str, array: np.array):
    """
    Method adapted from https://github.com/divideconcept/fastnumpyio/blob/main/fastnumpyio.py
        Write speeds go from 5ms using np.save to 1ms for game states using this code
    """
    array = np.asarray(array.tolist()[0])
    magic_string = b"\x93NUMPY\x01\x00v\x00"
    header = bytes(
        (
            "{'descr': '"
            + array.dtype.descr[0][1]
            + "', 'fortran_order': False, 'shape': "
            + str(array.shape)
            + ", }"
        ).ljust(127 - len(magic_string))
        + "\n",
        "utf-8",
    )
    with open(f"{filepath}.npy", "wb") as file:
        file.write(magic_string)
        file.write(header)
        file.write(array.tobytes())


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
