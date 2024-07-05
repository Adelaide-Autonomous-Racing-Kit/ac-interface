from configparser import ConfigParser
from pathlib import Path
from typing import Dict

from aci.config.constants import CONFIG_OVERRIDE_PATHS
from aci.utils.load import load_yaml
from loguru import logger


def configure_simulation(dynamic_configuration: Dict):
    """
    Sets Assetto Corsa configuration files to interface defaults then overrides any options
        the user has configured dynamically
    """
    set_default_launch_configurations()
    return override_default_configurations(dynamic_configuration)


def set_default_launch_configurations():
    """
    Combines the steam default race.ini with a yaml and writing it so AC launches
        with the set options
    """
    for override_file_name in CONFIG_OVERRIDE_PATHS:
        logger.info(f"Overriding {override_file_name} with package defaults")
        override_paths = CONFIG_OVERRIDE_PATHS[override_file_name]
        config = combine_configurations(override_paths.default, override_paths.override)
        write_ini(config, override_paths.user)
    logger.info("Launch configurations now set to package defaults")


def combine_configurations(default_path: Path, override_path: Path):
    """
    Combines a .ini and .yaml configuration using the .yaml to override options in
        the .ini
    """
    config = read_configuration(default_path)
    config.read_dict(load_yaml(override_path))
    return config


def write_ini(config: ConfigParser, output_path: Path):
    """
    Write out the .ini configuration file in the correct format for AC
    """
    with output_path.open("w") as file:
        config.write(file, space_around_delimiters=False)


def override_default_configurations(dynamic_configuration: Dict) -> Dict:
    """
    Overwrites any options specified by the user dynamically in the default settings
    """
    configs = {}
    for key in CONFIG_OVERRIDE_PATHS:
        if key in dynamic_configuration:
            configs[key] = override_configuration(dynamic_configuration[key], key)
        else:
            configs[key] = read_configuration(CONFIG_OVERRIDE_PATHS[key].user)
    return configs


def override_configuration(dynamic_configuration: Dict, filename: str) -> Dict:
    """
    Overwrites any options specified by the user dynamically in the default settings
    """
    override_path = CONFIG_OVERRIDE_PATHS[filename].user
    logger.info(f"User defined config for {filename} used: {dynamic_configuration}")
    config = override_configuration_with_dict(override_path, dynamic_configuration)
    write_ini(config, override_path)
    return ini_to_dict(config)


def ini_to_dict(config: ConfigParser) -> Dict:
    d = dict(config._sections)
    for k in d:
        d[k] = dict(config._defaults, **d[k])
        d[k].pop("__name__", None)
    return d


def override_configuration_with_dict(default_path: Path, override_config: Dict):
    """
    Combines a .ini with a python dictionary that overrides the .ini
    """
    config = read_configuration(default_path)
    config.read_dict(override_config)
    return config


def read_configuration(path: Path) -> ConfigParser:
    """
    Parses Assetto Corsa .ini files
    """
    config = create_ini_parser()
    config.read(path)
    return config


def create_ini_parser():
    """
    Creates a configuration parser for AC .ini files
    """
    config = ConfigParser()
    config.optionxform = lambda x: x
    return config
