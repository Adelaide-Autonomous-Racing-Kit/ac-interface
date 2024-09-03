import subprocess
from typing import List, Union

from aci.config.constants import CROSSOVER_AC_STEAM_APPID_FILE_PATH, STEAM_APPID
from aci.utils.data import Point
from aci.utils.os import move_application_window
from loguru import logger

LEFT_MENU_WIDTH = 100
BAR_TO_SETUP_NORMALISED_WIDTH = 0.078
SETUP_TO_FILE_WIDTH = 315
SETUP_TO_LOAD_WIDTH = 40


def launch_assetto_corsa_docker(window_position: Point, window_resolution: List[int]):
    """
    Launches AC in a crossover bottle
    """
    logger.info("Starting Assetto Corsa...")
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("launch_assetto_corsa\n")
    move_application_window("AC", window_resolution, window_position)


def shutdown_assetto_corsa_docker():
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("shutdown_assetto_corsa\n")


def launch_sate_server_docker() -> Union[subprocess.Popen, None]:
    """
    Launches a state server in the crossover bottle
    """
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("launch_state_server\n")


def shutdown_state_server_docker():
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("shutdown_state_server\n")


def maybe_create_steam_appid_file():
    """
    Ensures that the steam_appid.txt file is present and has the correct contents
        This file enables the game to launch without going via the launcher
    """
    if CROSSOVER_AC_STEAM_APPID_FILE_PATH.is_file():
        with CROSSOVER_AC_STEAM_APPID_FILE_PATH.open("r") as file:
            contents = file.read()
        if contents == STEAM_APPID:
            logger.info("Steam AppID file already present")
            return
    create_steam_appid_file()


def create_steam_appid_file():
    """
    Creates a file named steam_appid.txt containing the app ID 244210
    """
    logger.info("Creating Steam AppID file...")
    with CROSSOVER_AC_STEAM_APPID_FILE_PATH.open("w") as file:
        file.write(STEAM_APPID)
