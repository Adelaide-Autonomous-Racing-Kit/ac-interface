import argparse
from typing import Dict

from ruamel.yaml import YAML


def load_config() -> Dict:
    args = parse_arguments()
    return load_yaml(args.config)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="Path to configuration")
    return parser.parse_args()


def load_yaml(path: str) -> Dict:
    _yaml = YAML()
    with open(path) as file:
        params = _yaml.load(file)
    return params
