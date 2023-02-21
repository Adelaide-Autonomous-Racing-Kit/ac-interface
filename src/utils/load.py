from typing import Dict

import numpy as np
from src.game_capture.state.shared_memory.ac.combined import COMBINED_DATA_TYPES
import yaml

STRING_KEYS = [
    "tyre_compound",
    "last_time",
    "best_time",
    "split",
    "current_time",
]


def load_yaml(filepath: str) -> Dict:
    """
    Loads a yaml file as a dictionary
    """
    with open(filepath) as file:
        yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
    return yaml_dict


def load_game_state(filepath: str) -> Dict:
    """
    Loads recorded game state np.arrays as a dictionary of observations
        see src.game_capture.state.shared_memory.ac for a list of keys
    """
    with open(filepath, "rb") as file:
        data = file.read()
    return state_bytes_to_dict(data)


def state_bytes_to_dict(data: bytes) -> Dict:
    """
    Converts a game state np.arrays to a dictionary of observations
        see src.game_capture.state.shared_memory for a list of keys
    """
    state_array = np.frombuffer(data, COMBINED_DATA_TYPES)
    state_dict = {
        key[0]: value for key, value in zip(COMBINED_DATA_TYPES, state_array[0])
    }
    for string_key in STRING_KEYS:
        state_dict[string_key] = state_dict[string_key].tobytes().decode("utf-8")
    return state_dict
