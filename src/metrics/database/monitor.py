import multiprocessing as mp
import time
from typing import Dict

from loguru import logger
from src.metrics.database.postgres import PostgresConnector
from src.metrics.database.sql import get_select_interval_max_sql


class Evaluator(mp.Process):
    def __init__(self, evaluation_config: Dict, postgres_config: Dict):
        super().__init__()
        self._evaluation_config = evaluation_config
        self._postgres_db = PostgresConnector(postgres_config)
        self._current_lap = 0
        self._sql_queries = {}
        self.__setup_sql_queries()
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

        :is_running: True if the agent is counting this lap towards its submission,
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
        for sql_query_name, sql_query in self._sql_queries.items():
            data = self._query_database(sql_query)
            logger.info(sql_query_name)
            logger.info(data)

    def _query_database(self, query: str):
        data = None
        with self._postgres_db._session.cursor() as cursor:
            try:
                cursor.execute(query)
                data = cursor.fetchall()
            except Exception as e:
                logger.error(f"Monitor database query error: {e}")
                self._postgres_db._session.rollback()
        return data

    def __setup_processes_shared_memory(self):
        self._is_evaluation_lap = mp.Value("i", False)
        self._is_running = mp.Value("i", True)

    def __setup_sql_queries(self):
        table_name = self._postgres_db._table_name
        for monitor_info in self._evaluation_config["monitors"]:
            for interval_name, interval in monitor_info["intervals"].items():
                sql_query = get_select_interval_max_sql(
                    table_name,
                    [monitor_info["column"]],
                    monitor_info["interval_column"],
                    interval,
                    self._current_lap,
                )
                self._sql_queries[interval_name] = sql_query
                logger.info(interval_name)
                logger.info(sql_query)
