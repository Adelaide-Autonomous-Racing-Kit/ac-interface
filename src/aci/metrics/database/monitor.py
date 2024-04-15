import multiprocessing as mp
import time
import signal
from typing import Dict

from aci.metrics.database.postgres import PostgresConnector
from aci.metrics.database.trackers import TRACKER_TYPES
from loguru import logger
import psycopg


class Evaluator(mp.Process):
    def __init__(self, evaluation_config: Dict, postgres_config: Dict):
        super().__init__()
        self._evaluation_config = evaluation_config
        self._postgres_db = PostgresConnector(postgres_config)
        self._current_lap = 0
        self._sql_queries = {}
        self.__setup_trackers()
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
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while self._is_running:
            self._evaluate_agent()
            time.sleep(0.5)

    def stop(self):
        """
        Stops the evaluation process
        """
        self.is_running = False

    @property
    def _db_connection(self) -> psycopg.Connection:
        return self._postgres_db._session

    def _evaluate_agent(self):
        data = self._maybe_query_database()
        for interval_name, value in data.items():
            logger.info(f"{interval_name}: {value}")

    def _maybe_query_database(self):
        data = {}
        try:
            self._query_database(data)
        except Exception as e:
            logger.error(f"Monitor database query error: {e}")
            self._db_connection.rollback()
        return data

    def _query_database(self, data: Dict):
        with self._db_connection.pipeline():
            with self._db_connection.cursor() as cursor:
                self._submit_queries(cursor)
                self._get_results(cursor, data)

    def _submit_queries(self, cursor: psycopg.ServerCursor):
        for tracker in self._trackers.values():
            query = tracker.get_sql_query()
            cursor.execute(query["query"], query["to_bind"])

    def _get_results(self, cursor: psycopg.ServerCursor, data: Dict):
        for query_name, _ in self._trackers.items():
            data[query_name] = cursor.fetchall()
            cursor.nextset()

    def __setup_processes_shared_memory(self):
        self._is_evaluation_lap = mp.Value("i", False)
        self._is_running = mp.Value("i", True)

    def __setup_trackers(self):
        self._trackers = {}
        table_name = self._postgres_db._table_name
        for monitor_info in self._evaluation_config["monitors"]:
            for interval_name, interval in monitor_info["intervals"].items():
                tracker = TRACKER_TYPES[monitor_info["type"]](
                    interval,
                    monitor_info["interval_column"],
                    table_name,
                    monitor_info["column"],
                )
                tracker_name = "-".join([monitor_info["name"], interval_name])
                self._trackers[tracker_name] = tracker
