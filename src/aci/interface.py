import abc
import copy
import subprocess
import tempfile
import time
from typing import Dict, List

from aci.config.ac_config import configure_simulation
from aci.game_capture.inference import GameCapture
from aci.game_capture.state.client import StateClient
from aci.input.controller import VirtualGamepad
from aci.metrics.database.monitor import Evaluator
from aci.metrics.database.state_logger import DatabaseStateLogger
from aci.utils.data import Point
from aci.utils.launch import (
    launch_assetto_corsa,
    maybe_create_steam_appid_file,
    shutdown_assetto_corsa,
    start_session,
    try_until_state_server_is_launched,
)
from aci.utils.os import get_default_window_location
from loguru import logger
import numpy as np


class AssettoCorsaInterface(abc.ABC):
    """
    Abstract base class to inherit from when creating vehicle control agents
    """

    def __init__(self, config: Dict):
        # self._config["postgres"] = {
        #    "dbname": "postgres",
        #    "user": "postgres",
        #    "password": "postgres",
        #    "host": "0.0.0.0",
        #    "port": "5432",
        #    "table_name": "table" + next(tempfile._get_candidate_names()),
        # }
        # self._config["evaluation"] = {"monitors": [
        #         # Lap time and sectors monitor
        #         {
        #             "name": "time",
        #             "type": "maximum_interval",
        #             "column": "i_current_time",
        #             "interval_column": "normalised_car_position",
        #             "intervals": {
        #                 "lap": [0.0, 1.0],
        #                 "sector_1": [0.0, 0.3],
        #                 "sector_2": [0.3, 0.6],
        #                 "sector_3": [0.6, 1.0],
        #             },
        #         },
        #         # Average Speed monitor
        #         {
        #             "name": "speed",
        #             "type": "average_interval",
        #             "column": "speed_kmh",
        #             "interval_column": "normalised_car_position",
        #             "intervals": {configure_simulation],
        #                 "sector_3": [0.6, 1.0],
        #             },
        #         },
        #         # Minimum fuel monitor
        #         {
        #             "name": "fuel",
        #             "type": "minimum_interval",
        #             "column": "fuel",
        #             "interval_column": "normalised_car_position",
        #             "intervals": {
        #                 "lap": [0.0, 1.0],
        #                 "sector_1": [0.0, 0.3],
        #                 "sector_2": [0.3, 0.6],
        #                 "sector_3": [0.6, 1.0],
        #             },
        #         },
        #         # 5 lap average monitor
        #         # {
        #         #    "name": "time",
        #         #    "column": "i_current_time",
        #         #    "interval_column": "n_completed_laps",
        #         #    "intervals": {
        #         #        "last_5_laps": [0, 5],
        #         #    },
        #         #    "by": "n_completed_laps",
        #         # },
        #     ]
        # },
        # ]}
        self._setup(config)
        self.is_running = True

    def _setup(self, config: Dict):
        self._config = copy.deepcopy(config)
        self._initialise_AC()
        self._initialise_capture()
        self._initialise_evaluation()
        self._setup_termination_check()

    def _setup_termination_check(self):
        self._n_steps_since_last_check = 0
        termination_config = self._config.get("termination", {})
        self._n_steps_between_checks = termination_config.get("check_every_n", -1)
        self._n_consecutive_failures = 0
        max_consecutive_failures = termination_config.get("max_consecutive_failures", 0)
        self._n_max_consecutive_failures = max_consecutive_failures

    def _initialise_AC(self):
        maybe_create_steam_appid_file()
        simulation_config = configure_simulation(self._config)
        self._config.update(simulation_config)

    def _initialise_capture(self):
        try_until_state_server_is_launched()
        self._game_capture = GameCapture(self._config)
        self._input_interface = VirtualGamepad()

    def _initialise_evaluation(self):
        self._setup_database_logger()
        self._setup_evaluator()

    def _setup_database_logger(self):
        if "postgres" in self._config:
            config = self._config["postgres"]
            self._database_logger = DatabaseStateLogger(self._game_capture, config)
        else:
            self._database_logger = None

    def _setup_evaluator(self):
        if "evaluation" in self._config:
            evaluation_config = self._config["evaluation"]
            postgres_config = self._config["postgres"]
            self._evaluator = Evaluator(evaluation_config, postgres_config)
        else:
            self._evaluator = None

    def _launch_AC(self):
        is_started = False
        while not is_started:
            launch_assetto_corsa(self._window_location, self._window_resolution)
            state_client = StateClient()
            is_started = state_client.wait_until_AC_is_ready()
            if not is_started:
                self._shutdown_AC()

    def _start_capture(self):
        self._game_capture.start()

    def _start_evaluation(self):
        if self._database_logger is not None:
            self._database_logger.start()
        if self._evaluator is not None:
            self._evaluator.start()

    @property
    def _window_resolution(self) -> List[int]:
        display_config = self._config["video.ini"]["VIDEO"]
        return [int(display_config["WIDTH"]), int(display_config["HEIGHT"])]

    @property
    def _window_location(self) -> Point:
        if self._is_dynamic_window_location:
            window_location = self._config["capture"]["images"]["window_location"]
            window_location = Point(x=window_location[0], y=window_location[1])
        else:
            window_location = get_default_window_location(self._window_resolution)
        return window_location

    @property
    def _is_dynamic_window_location(self) -> bool:
        try:
            self._config["capture"]["images"]["window_location"]
        except KeyError:
            return False
        return True

    def _shutdown(self):
        self._game_capture.stop()
        self._stop_evaluator()
        self._stop_database_logger()
        self._shutdown_AC()

    def _stop_database_logger(self):
        if self._database_logger is not None:
            self._database_logger.stop()

    def _stop_evaluator(self):
        if self._evaluator is not None:
            self._evaluator.stop()

    def _shutdown_AC(self):
        shutdown_assetto_corsa()

    def run(self):
        self._launch_AC()
        self._start_capture()
        self._start_evaluation()
        start_session(self._window_resolution)
        time.sleep(2)
        while self.is_running:
            try:
                observation = self.get_observation()
                if self._is_termination_condition_met(observation):
                    self.is_running = False
                action = self.behaviour(observation)
                self.act(action)
            except KeyboardInterrupt:
                self.is_running = False
            except Exception as e:
                self._log_exception(e)
                self.is_running = False
        self.teardown()
        self._shutdown()

    def _is_termination_condition_met(self, observation: Dict) -> bool:
        if self._n_steps_between_checks < 0:
            return False
        if self._n_steps_between_checks > self._n_steps_since_last_check:
            self._n_steps_since_last_check += 1
            return False
        self._n_steps_since_last_check = 0
        if self.termination_condition(observation):
            self._n_consecutive_failures += 1
        else:
            self._n_consecutive_failures = 0
        if self._n_consecutive_failures >= self._n_max_consecutive_failures:
            message = "Agent has met the termination condition "
            message += f"{self._n_consecutive_failures} times. Terminating execution"
            logger.error(message)
            return True
        return False

    def _log_exception(self, exception: Exception):
        message = "Agent has thrown an exception and will now terminate. "
        message += f"Exception: {exception}"
        logger.error(message)

    def stop(self):
        """
        Signal the interface to stop running and clean up any processes
        """
        self.is_running = False

    def get_observation(self) -> Dict:
        """
        Get the latest captured game state from the simulation. From a list of keys
            present in the game state dictionary see aci/game_capture/state/shared_memory.py

        :return: {Dictionary image: BGR image as np.array, state: Dict{str: float}}
        :rtype: Dict[str: np.array, Dict]
        """
        return self._game_capture.capture

    def act(self, action: np.array):
        """
        Submits and action to the simulator. Throttle and brake are float values between
            {0.0, 1.0}. Steering angles are normalised float values between {-1.0, 1.0}.
            Where -1.0 represents full lock to the left and 1.0 full lock to the right.

        :action: An array in the format [steering angle, throttle, brake]
        :type: np.array
        """
        self._input_interface.submit_action(action)

    @abc.abstractmethod
    def behaviour(self, observation: Dict) -> np.array:
        """
        Define this method in your agent class that inherits from this class
            Accepts a dictionary of observations and returns a numpy array of
            actions.

        :observation: {Dictionary image: BGR image as np.array, state: Dict{str: float}}
        :type: Dict[str: np.array]
        :return: An array in the format [steering angle, throttle, brake]
        :rtype: np.array
        """

    @abc.abstractmethod
    def teardown(self):
        """
        Define this method in your agent class that inherits from this class
            Teardown any running processes or write out final logs here
        """

    @abc.abstractmethod
    def termination_condition(self, observation: Dict) -> bool:
        """
        Implement a condition based on simulation observation that is met will cause
            the current experiment to terminate

        :observation: {Dictionary image: BGR image as np.array, state: Dict{str: float}}
        :type: Dict[str: np.array]
        :return: True to terminate agent execution, False to continue
        :rtype: bool
        """
