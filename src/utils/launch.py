import os
import time
import pyautogui
from pathlib import Path

import subprocess
from loguru import logger


from src.game_capture.state.client import StateClient
from src.utils.os import get_application_window_coordinates
from src.config.constants import AC_STEAM_PATH, AC_STEAM_APPID_FILE_PATH, STEAM_APPID


def launch_assetto_corsa():
    """
    Launches AC in a crossover bottle
    """
    logger.info(f"Starting Assetto Corsa...")
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


def try_until_state_server_is_launched():
    """
    Continues to start state server subprocesses until a client is able to
        bind to one
    """
    is_running = False
    while not is_running:
        try:
            logger.info("Attempting to start State Server")
            p_state_server = launch_sate_server()
            time.sleep(2)
            _ = StateClient()
            is_running = True
        except ConnectionRefusedError:
            p_state_server.terminate()
    logger.info("State Server Started")


def launch_sate_server():
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
    p_state_server.stdin.write("python ./src/game_capture/state/server.py\n".encode())
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


def click_drive():
    """
    Clicks in the AC window on the drive button to start the session
    """
    top_left_corner = get_application_window_coordinates("AC", [1920, 1080])
    pyautogui.click(top_left_corner.x + 20, top_left_corner.y + 150)
