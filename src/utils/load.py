from typing import Dict
import yaml


def load_yaml(filepath: str) -> Dict:
    with open(filepath) as file:
        yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
    return yaml_dict
