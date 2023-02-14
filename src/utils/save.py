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
