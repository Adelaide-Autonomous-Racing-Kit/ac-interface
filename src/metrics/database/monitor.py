import multiprocessing as mp
import time
from typing import Dict

from loguru import logger
from src.metrics.database.postgres import PostgresConnector


class Evaluator(mp.Process):
    def __init__(self, evaluation_config: Dict, postgres_config: Dict):
        super().__init__()
        self._postgres_db = PostgresConnector(postgres_config)
        self.__setup_processes_shared_memory()

    @property
    def is_running(self) -> bool:
        """
        Checks if the evaluation process is running

        :return: True if the evaluation process is running, false if it is not
        :rtype: bool
        """
        with self._is_running.get_lock():
            is_running = self._is_running.value
        return is_running

    @is_running.setter
    def is_running(self, is_running: bool):
        """
        Sets whether the evaluation processes is running or noe

        :is_running: True if the evaluation process is running, false if it is not
        :type is_running: bool
        """
        with self._is_running.get_lock():
            self._is_running.value = is_running

    @property
    def is_evaluation_lap(self) -> bool:
        """
        Checks if the agent is counting this lap towards its submission

        :return: True if the agent is counting this lap towards its submission,
            false if it is not
        :rtype: bool
        """
        with self._is_evaluation_lap.get_lock():
            is_evaluation_lap = self._is_evaluation_lap.value
        return is_evaluation_lap

    @is_evaluation_lap.setter
    def is_evaluation_lap(self, is_evaluation_lap: bool):
        """
        Sets if the capture process is running

        :is_running: True if tthe agent is counting this lap towards its submission,
            false if it is not
        :type is_running: bool
        """
        with self._is_evaluation_lap.get_lock():
            self._is_evaluation_lap.value = is_evaluation_lap

    def run(self):
        """
        Called on Evaluator.start()
        """
        while self._is_running:
            self._evaluate_agent()
            time.sleep(0.5)

    def stop(self):
        """
        Stops the evaluation process
        """
        self.is_running = False

    def _evaluate_agent(self):
        logger.info("Agent is alive")
        logger.info(f"Is evaluation lap: {self.is_evaluation_lap}")
        logger.info(f"Is evaluation running: {self.is_running}")

    def __setup_processes_shared_memory(self):
        self._is_evaluation_lap = mp.Value("i", False)
        self._is_running = mp.Value("i", True)
