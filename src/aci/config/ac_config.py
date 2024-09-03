from collections import namedtuple
from configparser import ConfigParser
from pathlib import Path
from typing import Dict

from aci.config.constants import ACI_DEFAULT_CONFIG_PATH, CONFIG_FILES, CONFIG_PATHS
from aci.utils.load import load_yaml
from loguru import logger


OverridePaths = namedtuple("OverridePaths", "default user override")


class AssettoCorsaConfigurator:
    def __init__(self, config: Dict):
        self.__setup(config)

    def configure(self) -> Dict:
        """
        Sets Assetto Corsa configuration files to interface defaults then overrides any options
            the user has configured dynamically
        """
        self._restore_default_launch_configurations()
        return self._override_default_configurations()

    @property
    def _is_recording(self) -> bool:
        return "recording" in self._config

    @property
    def _is_proton(self) -> bool:
        return self._config["capture"]["is_proton"]

    def _restore_default_launch_configurations(self):
        """
        Combines the steam default race.ini with a yaml and writing it so AC launches
            with the set options
        """
        for override_file_name in self._config_override_paths:
            if override_file_name == "controls.ini" and self._is_recording:
                continue
            logger.info(f"Overriding {override_file_name} with package defaults")
            override_paths = self._config_override_paths[override_file_name]
            config = combine_configurations(
                override_paths.default, override_paths.override
            )
            write_ini(config, override_paths.user)
        logger.info("Launch configurations now set to package defaults")

    def _override_default_configurations(self) -> Dict:
        """
        Overwrites any options specified by the user dynamically in the default settings
        """
        configs = {}
        for key in self._config_override_paths:
            if key in self._config:
                configs[key] = self._override_configuration(key)
            else:
                configs[key] = read_configuration(self._config_override_paths[key].user)
        return configs

    def _override_configuration(self, filename: str) -> Dict:
        """
        Overwrites any options specified by the user dynamically in the default settings
        """
        override_path = self._config_override_paths[filename].user
        config = self._config[filename]
        logger.info(f"User defined config for {filename} used: {config}")
        config = override_configuration_with_dict(override_path, config)
        write_ini(config, override_path)
        return ini_to_dict(config)

    def __setup(self, config: Dict):
        self._config = config
        self._setup_override_paths()

    def _setup_override_paths(self):
        self._config_override_paths = {}
        path_roots = self._get_override_path_roots()
        for filename in CONFIG_FILES:
            orverride_paths = self._get_override_path(path_roots, filename)
            self._config_override_paths[filename] = orverride_paths

    def _get_override_path_roots(self) -> Dict:
        if self._is_proton:
            override_path_roots = CONFIG_PATHS["proton"]
        else:
            override_path_roots = CONFIG_PATHS["crossover"]
        return override_path_roots

    def _get_override_path(self, path_roots: Dict, filename: str) -> OverridePaths:
        filename_yaml = filename.replace(".ini", ".yaml")
        deafult_path = Path(path_roots["steam"], filename)
        user_path = Path(path_roots["user"], filename)
        override_path = Path(ACI_DEFAULT_CONFIG_PATH, filename_yaml)
        return OverridePaths(deafult_path, user_path, override_path)


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
