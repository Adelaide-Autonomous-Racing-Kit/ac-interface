from typing import Dict

from .base import AssettoCorsaLauncher
from .crossover import CrossOverLauncher, DockerCrossOverLauncher
from .proton import DockerProtonLauncher, ProtonLauncher

AC_LAUNCHERS = {
    "proton": {
        "docker": DockerProtonLauncher,
        "metal": ProtonLauncher,
    },
    "crossover": {
        "docker": DockerCrossOverLauncher,
        "metal": CrossOverLauncher,
    },
}


def get_ac_launcher(config: Dict) -> AssettoCorsaLauncher:
    is_proton = config["capture"]["is_proton"]
    comptability_tool = "proton" if is_proton else "crossover"
    is_docker = config["capture"]["is_docker"]
    executor = "docker" if is_docker else "metal"
    return AC_LAUNCHERS[comptability_tool][executor](config)
