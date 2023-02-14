import glob
import pathlib
from typing import List, Tuple

from PIL import Image
from loguru import logger
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from src.utils.load import load_game_state


def load_sample_file(
    sample_file_path_pair: Tuple[pathlib.Path, pathlib.Path]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loads the JPEG and corresponding NPY file from the specified sample file path,
    and returns the loaded images as NumPy arrays.
    """
    jpeg_file, npy_file = sample_file_path_pair
    jpeg_image = np.array(Image.open(jpeg_file))
    game_state = load_game_state(npy_file)
    return jpeg_image, game_state


def get_sample_file_paths(directory: str) -> List[Tuple[pathlib.Path, pathlib.Path]]:
    """
    Finds all the JPEG and corresponding NPY files in the specified directory,
    and returns a list of tuples containing the file paths.
    """
    jpeg_files = list(pathlib.Path(directory).glob("*.jpeg"))
    jpeg_files.sort(key=lambda path: int(path.stem))

    sample_file_paths = []
    for jpeg_file in jpeg_files:
        npy_file = jpeg_file.with_suffix(".npy")
        if npy_file.exists():
            sample_file_paths.append((jpeg_file, npy_file))
        else:
            logger.warning(
                f"Could not find corresponding .npy file for {jpeg_file}. Skipping file."
            )

    return sample_file_paths


if __name__ == "__main__":
    directory = "recordings/monza_audi_r8_lms"
    sample_file_paths = get_sample_file_paths(directory)

    # Extract relevant data from state dictionary at each time step
    positions = []
    for sample in sample_file_paths[:25]:
        img, state = load_sample_file(sample)
        x, y, z = state["velocity1"], state["velocity2"], state["velocity3"]
        pitch, roll, heading = state["pitch"], state["roll"], state["heading"]
        ax, ay, az = (
            state["acceleration_g_X"],
            state["acceleration_g_Y"],
            state["acceleration_g_Z"],
        )
        positions.append([x, y, z, pitch, roll, heading, ax, ay, az])

    ax = plt.axes(projection="3d")
    old_x, old_y, old_z = None, None, None
    for i, frame in enumerate(positions):
        x, y, z, _, _, _, _, _, _ = frame

        if old_x is None:
            old_x, old_y, old_z = x, y, z
            continue

        else:
            ax.plot3D([old_x, x], [old_y, y], [old_z, z], "gray")
            old_x, old_y, old_z = x, y, z

    plt.show()
