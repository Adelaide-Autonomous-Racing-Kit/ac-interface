import abc
import subprocess
import tempfile
import time
from typing import Dict

from loguru import logger
import numpy as np
from src.config.ac_config import override_launch_configurations
from src.game_capture.inference import GameCapture
from src.game_capture.state.client import StateClient
from src.input.controller import VirtualGamepad
from src.metrics.database.monitor import Evaluator
from src.metrics.database.state_logger import DatabaseStateLogger
from src.utils.launch import (
    click_drive,
    launch_assetto_corsa,
    maybe_create_steam_appid_file,
    try_until_state_server_is_launched,
)


class AssettoCorsaInterface(abc.ABC):
    """
    Abstract base class to inherit from when creating vehicle control agents
    """

    def __init__(self):
        self._config = {
            "postgres": {
                "dbname": "postgres",
                "user": "postgres",
                "password": "postgres",
                "host": "0.0.0.0",
                "port": "5432",
                "table_name": "table" + next(tempfile._get_candidate_names()),
            },
            "capture": {
                "use_rgb_images": False,
                "use_state_dicts": True,
            },
            "evaluation": {"monitors": []}
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
            #             "intervals": {
            #                 "lap": [0.0, 1.0],
            #                 "sector_1": [0.0, 0.3],
            #                 "sector_2": [0.3, 0.6],
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
        }
        self._setup()
        self.is_running = True

    def _setup(self):
        self._initialise_AC()
        self._initialise_capture()
        self._initialise_evaluation()

    def _initialise_AC(self):
        maybe_create_steam_appid_file()
        override_launch_configurations()

    def _initialise_capture(self):
        try_until_state_server_is_launched()
        self._game_capture = GameCapture(self._config)
        self._input_interface = VirtualGamepad()

    def _initialise_evaluation(self):
        postgres_config = self._config["postgres"]
        evaluation_config = self._config["evaluation"]
        self._database_logger = DatabaseStateLogger(self._game_capture, postgres_config)
        self._evaluator = Evaluator(evaluation_config, postgres_config)

    def _launch_AC(self):
        launch_assetto_corsa()
        state_client = StateClient()
        state_client.wait_until_AC_is_ready()

    def _start_capture(self):
        self._game_capture.start()

    def _start_evaluation(self):
        self._database_logger.start()
        self._evaluator.start()

    def shutdown(self):
        self._game_capture.stop()
        self._evaluator.stop()
        self._database_logger.stop()
        self._shutdown_AC()
        self._shutdown_python()

    def _shutdown_AC(self):
        subprocess.run(["pkill", "acs.exe"])

    def _shutdown_python(self):
        subprocess.run(["pkill", "python"])

    def run(self):
        self._launch_AC()
        self._start_capture()
        self._start_evaluation()
        click_drive()
        time.sleep(2)
        while self.is_running:
            try:
                # logger.info("Agent Action Loop")
                observation = self.get_observation()
                action = self.behaviour(observation)
                self.act(action)
            except KeyboardInterrupt:
                self.is_running = False
        self.shutdown()

    def get_observation(self) -> Dict:
        """
        Get the latest captured game state from the simulation. From a list of keys
            present in the game state dictionary see src/game_capture/state/shared_memory.py

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
    def setup(self):
        """
        Define this method in your agent class that inherits from this class
            Setup up any member variables, state and models your agent will need
        """
