import abc
import copy
import subprocess
import tempfile
import time
import traceback
from typing import Dict

from aci.game_capture.inference import GameCapture
from aci.input.controller import VirtualGamepad
from aci.launchers import get_ac_launcher
from aci.metrics.database.monitor import Evaluator
from aci.metrics.database.state_logger import DatabaseStateLogger
from aci.monitor import RestartMonitor, TerminationMonitor
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
        self._setup_monitors()

    def _setup_monitors(self):
        restart_config = self._config.get("restart", {})
        self._restart_monitor = RestartMonitor(restart_config, self)
        termination_config = self._config.get("termination", {})
        self._termination_monitor = TerminationMonitor(termination_config, self)

    def _initialise_AC(self):
        self._ac_launcher = get_ac_launcher(self._config)
        self._config.update(self._ac_launcher.config)

    def _initialise_capture(self):
        self._ac_launcher.launch_sate_server()
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
        self._ac_launcher.launch_assetto_corsa()

    def _start_capture(self):
        self._game_capture.start()

    def _start_evaluation(self):
        if self._database_logger is not None:
            self._database_logger.start()
        if self._evaluator is not None:
            self._evaluator.start()

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
        self._ac_launcher.shutdown_assetto_corsa()
        self._ac_launcher.shutdown_state_server()

    def run(self):
        self._launch_AC()
        self._start_capture()
        self._start_evaluation()
        self._start_session()
        while self.is_running:
            try:
                observation = self.get_observation()
                self._maybe_terminate_session(observation)
                action = self.behaviour(observation)
                self.act(action)
                self._maybe_restart_session(observation)
            except KeyboardInterrupt:
                self.is_running = False
            except Exception as e:
                self._log_exception(e)
                self.is_running = False
        self.teardown()
        self._shutdown()

    def _start_session(self):
        self._ac_launcher.start_session()
        time.sleep(2)

    def _maybe_terminate_session(self, observation: Dict):
        if self._termination_monitor.is_triggered(observation):
            self.is_running = False

    def _maybe_restart_session(self, observation: Dict):
        if self._restart_monitor.is_triggered(observation):
            self._restart_session()
            self.on_restart()

    def _restart_session(self):
        self.act(np.array([0.0, 0.0, 0.0]))
        self._ac_launcher.restart_session()
        self._termination_monitor.reset()
        self._restart_monitor.reset()
        time.sleep(2)

    def _log_exception(self, exception: Exception):
        message = traceback.format_exc()
        message += "Agent has thrown an exception and will now terminate. "
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
        self._input_interface.submit_action(action.copy())

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
        Implement a condition based on simulation observation that when met will cause
            the current experiment to terminate

        :observation: {Dictionary image: BGR image as np.array, state: Dict{str: float}}
        :type: Dict[str: np.array]
        :return: True to terminate agent execution, False to continue
        :rtype: bool
        """

    @abc.abstractmethod
    def restart_condition(self, observation: Dict) -> bool:
        """
        Implement a condition based on simulation observation that when met will cause
            the current session to be restarted

        :observation: {Dictionary image: BGR image as np.array, state: Dict{str: float}}
        :type: Dict[str: np.array]
        :return: True to restart the session, False to continue
        :rtype: bool
        """

    @abc.abstractmethod
    def on_restart(self):
        """
        Implement any reset procedures you would like to execute before the behaviour
            loop is resumed
        """

