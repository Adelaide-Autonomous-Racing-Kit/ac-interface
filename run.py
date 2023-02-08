import time
import os
import pyautogui
from pathlib import Path

import subprocess
from loguru import logger

from examples.random_agent import main as run_example
from src.game_capture.state.client import StateClient
from src.utils.os import get_application_window_coordinates
from src.config.constants import AC_STEAM_PATH
from src.config.ac_config import override_launch_configurations


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
        stdout=subprocess.PIPE,
    )
    os.chdir(original_dir)


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


def try_until_state_server_is_launched():
    """
    Continues to start state server subprocesses until a client is able to
        bind to one
    """
    is_running = False
    while not is_running:
        try:
            logger.info("Attempting to start StateServer")
            p_state_server = launch_sate_server()
            time.sleep(1)
            _ = StateClient()
            is_running = True
        except ConnectionRefusedError:
            p_state_server.terminate()
    logger.info("StateServer Started")


def click_drive():
    """
    Clicks in the AC window on the drive button to start the session
    """
    top_left_corner = get_application_window_coordinates("AC", [1920, 1080])
    pyautogui.click(top_left_corner.x + 20, top_left_corner.y + 150)


def main():
    """
    An Example of programatically launching the interface
    """
    ## Setup
    override_launch_configurations()
    launch_assetto_corsa()
    try_until_state_server_is_launched()
    # Could use packet ID to check if the simulation has
    # started posting to see if we can select drive yet?
    time.sleep(15)  # Wait for AC menu to load
    click_drive()
    ##

    # Random agent example
    run_example()

    ## Clean up processes
    subprocess.run(["pkill", "acs.exe"])
    subprocess.run(["pkill", "python"])


if __name__ == "__main__":
    main()
