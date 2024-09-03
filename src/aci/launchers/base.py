import abc
import time
from typing import Dict

from aci.config.ac_config import AssettoCorsaConfigurator
from aci.utils.data import Point
from aci.utils.os import (
    get_application_window_coordinates,
    get_default_window_location,
    move_application_window,
)
from acs.client import StateClient
from halo import Halo
from loguru import logger
import pyautogui

LEFT_MENU_WIDTH = 100
BAR_TO_SETUP_NORMALISED_WIDTH = 0.078
SETUP_TO_FILE_WIDTH = 315
SETUP_TO_LOAD_WIDTH = 40


class AssettoCorsaLauncher(abc.ABC):
    def __init__(self, config: Dict):
        self.__setup(config)

    @property
    def config(self) -> Dict:
        return self._config

    def launch_assetto_corsa(self):
        """
        Launches AC
        """
        with Halo(text="Starting Assetto Corsa...", spinner="line"):
            is_connected, is_started = False, False
            while not is_started:
                self._launch_assetto_corsa()
                while not is_connected:
                    is_connected = self._test_connection_to_server()
                    time.sleep(1)
                state_client = StateClient()
                is_started = state_client.wait_until_AC_is_ready()
                if not is_started:
                    self._shutdown_assetto_corsa()
                    self._shutdown_state_server()
                    is_connected = False
        self._move_assetto_corsa_window()

    @abc.abstractmethod
    def _launch_assetto_corsa(self):
        """
        Implement logic to launch AC
        """
        pass

    def _test_connection_to_server(self) -> bool:
        is_connected = False
        try:
            state_client = StateClient()
            is_connected = True
        except ConnectionRefusedError:
            pass
        if is_connected:
            state_client.stop()
        return is_connected

    def _move_assetto_corsa_window(self):
        location, resolution = self._window_location, self._window_resolution
        move_application_window("AC", resolution, location)

    def shutdown_assetto_corsa(self):
        """
        Shutdown AC
        """
        logger.info("Shutting Down Assetto Corsa...")
        self._shutdown_assetto_corsa()

    @abc.abstractmethod
    def _shutdown_assetto_corsa(self):
        """
        Implement logic to shutdown AC
        """
        pass

    def launch_sate_server(self):
        """
        Launch state server
        """
        with Halo(text="Starting State Server...", spinner="line"):
            self._launch_sate_server()
        logger.info("State Server Started")

    @abc.abstractmethod
    def _launch_sate_server(self):
        """
        Implement logic to launch state server
        """
        pass

    def shutdown_state_server(self):
        """
        Shutdown state server
        """
        self._shutdown_state_server()

    @abc.abstractmethod
    def _shutdown_state_server(self):
        """
        Implement logic to shutdown state server
        """
        pass

    def start_session(self):
        """
        Loads a vehicle setup and begins the simulation session
        """
        self._load_vehicle_setup()
        self.click_drive()

    def click_drive(self):
        """
        Clicks in the AC window on the drive button to start the session
        """
        cursor_location = pyautogui.position()
        top_left_corner = get_application_window_coordinates(
            "AC", self._window_resolution
        )
        pyautogui.click(top_left_corner.x + 20, top_left_corner.y + 150)
        pyautogui.moveTo(cursor_location)

    def _load_vehicle_setup(self):
        """
        Clicks in the AC window to load the vehicle setup in the top position of the UI
        """
        top_left_corner = get_application_window_coordinates(
            "AC", self._window_resolution
        )
        cursor_location = pyautogui.position()
        bar_to_setup_width = BAR_TO_SETUP_NORMALISED_WIDTH * self._window_resolution[0]
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

    def __setup(self, config: Dict):
        self._config = config
        self._configure_simulation()
        self._setup_window_resolution()
        self._setup_window_location()

    def _configure_simulation(self):
        self._config_manager = AssettoCorsaConfigurator(self._config)
        self._config.update(self._config_manager.configure())
        self._aditional_configuration()

    def _aditional_configuration(self):
        """
        Implement logic for any additional configuration of Assetto Corsa
        """
        pass

    def _setup_window_resolution(self):
        display_config = self._config["video.ini"]["VIDEO"]
        resolution = [int(display_config["WIDTH"]), int(display_config["HEIGHT"])]
        self._window_resolution = resolution

    def _setup_window_location(self) -> Point:
        if self._is_dynamic_window_location:
            window_location = self._config["capture"]["images"]["window_location"]
            window_location = Point(x=window_location[0], y=window_location[1])
        else:
            window_location = get_default_window_location(self._window_resolution)
        self._window_location = window_location

    @property
    def _is_dynamic_window_location(self) -> bool:
        try:
            self._config["capture"]["images"]["window_location"]
        except KeyError:
            return False
        return True
