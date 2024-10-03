from aci.config.constants import CROSSOVER_AC_STEAM_APPID_FILE_PATH, STEAM_APPID
from loguru import logger


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
