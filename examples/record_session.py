import argparse
from typing import Dict

from ruamel.yaml import YAML

from aci.recorder import AssettoCorsaRecorder


def main():
    args = parse_arguments()
    config = load_yaml(args.config)
    recorder = AssettoCorsaRecorder(config)
    recorder.run()


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="Path to configuration")
    return parser.parse_args()


def load_yaml(path: str) -> Dict:
    _yaml = YAML()
    with open(path) as file:
        params = _yaml.load(file)
    return params


if __name__ == "__main__":
    main()
