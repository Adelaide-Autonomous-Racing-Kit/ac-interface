from pathlib import Path
from typing import Dict, Union

from acs.shared_memory.ac.combined import COMBINED_DATA_TYPES
import cv2
import numpy as np
import yaml

STRING_KEYS = [
    "tyre_compound",
    "last_time",
    "best_time",
    "split",
    "current_time",
]


def load_yaml(filepath: Union[Path, str]) -> Dict:
    """
    Loads a yaml file as a dictionary.

    :param filepath: Path to yaml file to be loaded.
    :type filepath: Union[Path,str]
    :return: Load yaml file as a dictionary.
    :rtype: Dict
    """
    with open(filepath) as file:
        yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
    return yaml_dict


def load_game_state(filepath: Union[Path, str]) -> Dict:
    """
    Loads recorded game state as a dictionary of observations see
        aci.game_capture.state.shared_memory.ac for a list of keys.

    :param filepath: Path to game state binary file to be loaded.
    :type filepath: Union[Path,str]
    :return: Game state loaded as a dictionary.
    :rtype: Dict
    """
    with open(filepath, "rb") as file:
        data = file.read()
    return state_bytes_to_dict(data)


def state_bytes_to_dict(data: bytes) -> Dict:
    """
    Converts a byte array game state to a dictionary of observations see
        aci.game_capture.state.shared_memory for a list of keys.


    :param data: Byte array of game state.
    :type data: bytes
    :return: Game state as a dictionary.
    :rtype: Dict
    """
    state_array = np.frombuffer(data, COMBINED_DATA_TYPES)
    state_dict = {
        key[0]: value.tobytes().decode("utf-8") if key in STRING_KEYS else value
        for key, value in zip(COMBINED_DATA_TYPES, state_array[0])
    }
    return state_dict


def load_image(filepath: Union[Path, str]) -> np.array:
    """
    Loads an image from file.

    :param filepath: Path to image file to be loaded.
    :type filepath: Union[Path,str]
    :return: Image loaded as a numpy array.
    :rtype: np.array
    """
    if isinstance(filepath, Path):
        filepath = str(filepath)
    return cv2.imread(filepath)
