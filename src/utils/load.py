from typing import Dict
import numpy as np
import yaml

from game_capture.state.shared_memory.physics import PhysicsSharedMemory


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
        see src.game_capture.state.shared_memory for a list of keys
    """
    state = np.load(filepath)
    return state_array_to_dict(state)


def state_array_to_dict(state_array: np.array) -> Dict:
    """
    Converts a game state np.arrays to a dictionary of observations
        see src.game_capture.state.shared_memory for a list of keys
    """
    return {
        key[0]: value for key, value in zip(PhysicsSharedMemory._fields_, state_array)
    }
