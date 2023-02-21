from configparser import ConfigParser
from pathlib import Path

from loguru import logger
from src.config.constants import (
    AC_OVERRIDE_RACE_INI_YAML_PATH,
    AC_USER_RACE_INI_PATH,
    CONFIG_OVERRIDE_PATHS,
    DEFAULT_RACE_INI_PATH,
)
from src.utils.load import load_yaml


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


def override_launch_configurations():
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


if __name__ == "__main__":
    override_launch_configurations()
