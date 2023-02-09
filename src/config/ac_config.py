from pathlib import Path

from configparser import ConfigParser
from loguru import logger

from src.utils.load import load_yaml
from src.config.constants import (
    DEFAULT_RACE_INI_PATH,
    AC_USER_RACE_INI_PATH,
    AC_OVERRIDE_RACE_INI_YAML_PATH,
)


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
    logger.info("Overriding launch configurations with package defaults...")
    config = combine_configurations(
        DEFAULT_RACE_INI_PATH,
        AC_OVERRIDE_RACE_INI_YAML_PATH,
    )
    write_ini(config, AC_USER_RACE_INI_PATH)
    logger.info("Launch configurations now set to package defaults")


if __name__ == "__main__":
    override_launch_configurations()
