from configparser import ConfigParser
from pathlib import Path
from typing import Dict

from aci.config.constants import CONFIG_OVERRIDE_PATHS
from aci.utils.load import load_yaml
from loguru import logger


def create_ini_parser():
    """
    Creates a configuration parser for AC .ini files
    """
    config = ConfigParser()
    config.optionxform = lambda x: x
    return config


def write_ini(config: ConfigParser, output_path: Path):
    """
    Write out the .ini configuration file in the correct format for AC
    """
    with output_path.open("w") as file:
        config.write(file, space_around_delimiters=False)


def combine_configurations(default_path: Path, override_path: Path):
    """
    Combines a .ini and .yaml configuration using the .yaml to override options in
        the .ini
    """
    config = create_ini_parser()
    config.read(default_path)
    config.read_dict(load_yaml(override_path))
    return config


def set_default_launch_configurations():
    """
    An example of combining thr steam default race.ini with a yaml and writing
        it so AC launches with the set options
    """
    for override_file_name in CONFIG_OVERRIDE_PATHS:
        logger.info(f"Overriding {override_file_name} with package defaults")
        override_paths = CONFIG_OVERRIDE_PATHS[override_file_name]
        config = combine_configurations(override_paths.default, override_paths.override)
        write_ini(config, override_paths.user)
    logger.info("Launch configurations now set to package defaults")


def override_race_configuration(race_configuration: Dict):
    override_paths = CONFIG_OVERRIDE_PATHS["race.ini"]
    logger.info(f"User defined race config used: {race_configuration}")
    race_configuration = {"RACE": race_configuration}
    config = override_configuration_with_dict(override_paths.user, race_configuration)
    write_ini(config, override_paths.user)


def override_configuration_with_dict(default_path: Path, override_config: Dict):
    """
    Combines a .ini with a python dictionary that overrides the .ini
    """
    config = create_ini_parser()
    config.read(default_path)
    config.read_dict(override_config)
    return config


if __name__ == "__main__":
    set_default_launch_configurations()
