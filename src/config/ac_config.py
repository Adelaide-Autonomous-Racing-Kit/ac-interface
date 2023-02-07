from pathlib import Path

from configparser import ConfigParser

from src.utils.load import load_yaml


def create_ini_parser():
    config = ConfigParser()
    config.optionxform = lambda x: x
    return config


def write_ini(config: ConfigParser, output_path: Path):
    with output_path.open("w") as file:
        config.write(file, space_around_delimiters=False)


def combine_configurations(default_path: Path, override_path: Path):
    config = create_ini_parser()
    config.read(default_path)
    config.read_dict(load_yaml(override_path))
    return config


def main():
    root_path = Path(Path.home(), ".cxoffice/Assetto_Corsa/drive_c")
    default_config_path = Path(
        root_path,
        "Program Files (x86)/Steam/steamapps/common/assettocorsa/cfg/race.ini",
    )
    user_config_path = Path(
        root_path,
        "users/crossover/Documents/Assetto Corsa/cfg/race.ini",
    )
    override_yaml_path = Path("./src/config/simulation/race.yaml")

    config = combine_configurations(default_config_path, override_yaml_path)
    write_ini(config, user_config_path)


if __name__ == "__main__":
    main()
