import os
from pathlib import Path
import subprocess
import time
from typing import List, Union

from aci.config.constants import (
    AC_STEAM_APPID_FILE_PATH,
    AC_STEAM_PATH,
    GAME_NAME_TO_WINDOW_NAME,
    STEAM_APPID,
)
from aci.game_capture.state.client import StateClient
from aci.utils.os import get_application_window_coordinates
from halo import Halo
from loguru import logger
import pyautogui


def launch_assetto_corsa():
    """
    Launches AC in a crossover bottle
    """
    logger.info("Starting Assetto Corsa...")
    original_dir = Path.cwd()
    os.chdir(AC_STEAM_PATH)
    subprocess.Popen(
        [
            "/opt/cxoffice/bin/wine",
            "--bottle",
            "Assetto_Corsa",
            "--cx-app",
            "acs.exe",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    os.chdir(original_dir)


def try_until_state_server_is_launched() -> Union[subprocess.Popen, None]:
    """
    Continues to start state server subprocesses until a client is able to
        bind to one
    """
    is_running, p_state_server = False, None
    try:
        # Is a state server already active
        state_client = StateClient()
        is_running = True
    except ConnectionRefusedError:
        pass
    while not is_running:
        with Halo(text="Starting State Server...", spinner="line"):
            try:
                p_state_server = launch_sate_server()
                time.sleep(2)
                state_client = StateClient()
                is_running = True
            except ConnectionRefusedError:
                p_state_server.terminate()
    state_client.stop()
    logger.info("State Server Started")
    return p_state_server


def launch_sate_server() -> subprocess.Popen:
    """
    Launches a state server in the crossover bottle
    """
    p_state_server = subprocess.Popen(
        [
            "/opt/cxoffice/bin/wine",
            "--bottle",
            "Assetto_Corsa",
            "--cx-app",
            "cmd.exe",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    p_state_server.stdin.write("python -m aci.game_capture.state.server\n".encode())
    return p_state_server


def maybe_create_steam_appid_file():
    """
    Ensures that the steam_appid.txt file is present and has the correct contents
        This file enables the game to launch without going via the launcher
    """
    if AC_STEAM_APPID_FILE_PATH.is_file():
        with AC_STEAM_APPID_FILE_PATH.open("r") as file:
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
    with AC_STEAM_APPID_FILE_PATH.open("w") as file:
        file.write(STEAM_APPID)


def click_drive(window_resolution: List[int]):
    """
    Clicks in the AC window on the drive button to start the session
    """
    top_left_corner = get_application_window_coordinates("AC", window_resolution)
    cursor_location = pyautogui.position()
    pyautogui.click(top_left_corner.x + 20, top_left_corner.y + 150)
    pyautogui.moveTo(cursor_location)
