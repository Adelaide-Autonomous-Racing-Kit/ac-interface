import os
from pathlib import Path
import subprocess
import time
from typing import List, Union

from aci.config.constants import AC_STEAM_APPID_FILE_PATH, AC_STEAM_PATH, STEAM_APPID
from aci.game_capture.state.client import StateClient
from aci.utils.data import Point
from aci.utils.os import get_application_window_coordinates, move_application_window
from halo import Halo
from loguru import logger
import pyautogui

LEFT_MENU_WIDTH = 100
BAR_TO_SETUP_NORMALISED_WIDTH = 0.078
SETUP_TO_FILE_WIDTH = 315
SETUP_TO_LOAD_WIDTH = 40


def launch_assetto_corsa(window_position: Point, window_resolution: List[int]):
    """
    Launches AC in a crossover bottle
    """
    logger.info("Starting Assetto Corsa...")
    # TODO: Make this work in and out of docker
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("launch_assetto_corsa\n")
    # original_dir = Path.cwd()
    # os.chdir(AC_STEAM_PATH)
    # subprocess.Popen(
    #     [
    #         "/opt/cxoffice/bin/wine",
    #         "--bottle",
    #         "Assetto_Corsa",
    #         "--cx-app",
    #         "acs.exe",
    #     ],
    #     stdin=subprocess.PIPE,
    #     stdout=subprocess.DEVNULL,
    #     stderr=subprocess.PIPE,
    # )
    # os.chdir(original_dir)
    move_application_window("AC", window_resolution, window_position)


def shutdown_assetto_corsa():
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("shutdown_assetto_corsa\n")


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
                launch_sate_server()
                time.sleep(2)
                state_client = StateClient()
                is_running = True
            except ConnectionRefusedError:
                shutdown_state_server()
                # p_state_server.terminate()
    state_client.stop()
    logger.info("State Server Started")
    return p_state_server


def launch_sate_server() -> Union[subprocess.Popen, None]:
    """
    Launches a state server in the crossover bottle
    """
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("launch_state_server\n")
    # p_state_server = subprocess.Popen(
    #     [
    #         "/opt/cxoffice/bin/wine",
    #         "--bottle",
    #         "Assetto_Corsa",
    #         "--cx-app",
    #         "cmd.exe",
    #     ],
    #     stdin=subprocess.PIPE,
    #     stdout=subprocess.PIPE,
    # )
    # p_state_server.stdin.write("python -m aci.game_capture.state.server\n".encode())
    # return p_state_server


def shutdown_state_server():
    with open("/execution_pipes/aci_execution_pipe", "w") as f:
        f.write("shutdown_state_server\n")


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


def start_session(window_resolution: List[int]):
    """
    Loads a vehicle setup and begins the simulation session
    """
    load_vehicle_setup(window_resolution)
    click_drive(window_resolution)


def click_drive(window_resolution: List[int]):
    """
    Clicks in the AC window on the drive button to start the session
    """
    cursor_location = pyautogui.position()
    top_left_corner = get_application_window_coordinates("AC", window_resolution)
    pyautogui.click(top_left_corner.x + 20, top_left_corner.y + 150)
    pyautogui.moveTo(cursor_location)


def load_vehicle_setup(window_resolution: List[int]):
    """
    Clicks in the AC window to load the vehicle setup in the top position of the UI
    """
    top_left_corner = get_application_window_coordinates("AC", window_resolution)
    cursor_location = pyautogui.position()
    bar_to_setup_width = BAR_TO_SETUP_NORMALISED_WIDTH * window_resolution[0]
    base_x_offset = LEFT_MENU_WIDTH + bar_to_setup_width
    # Click setup menu
    pyautogui.click(top_left_corner.x + 20, top_left_corner.y + 275)
    # Click setup in top position (alphabetical)
    x_offset = base_x_offset + SETUP_TO_FILE_WIDTH
    pyautogui.click(top_left_corner.x + x_offset, top_left_corner.y + 180)
    # Click load setup
    x_offset = base_x_offset + SETUP_TO_LOAD_WIDTH
    pyautogui.click(top_left_corner.x + x_offset, top_left_corner.y + 500)
    pyautogui.moveTo(cursor_location)
    # Wait for setup to validate
    time.sleep(2)
