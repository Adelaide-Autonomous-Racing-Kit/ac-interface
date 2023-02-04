from typing import Dict
import numpy as np
import yaml

from src.game_capture.state.shared_memory import SHMStruct


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
    game_state = {key[0]: value for key, value in zip(SHMStruct._fields_, state)}
    return game_state
