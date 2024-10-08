from datetime import datetime
from functools import partial
import multiprocessing as mp
import signal
from typing import Dict

from aci.metrics.database.postgres import PostgresConnector
from aci.metrics.database.sql import get_create_table_sql, get_insert_row_sql
from aci.utils.load import state_bytes_to_dict
from loguru import logger
import numpy as np
import psycopg

NUMPY_TO_PYTHON_DTYPES = {
    np.int32: int,
    np.int64: int,
    np.float32: float,
    np.float64: float,
}


class DatabaseStateLogger(mp.Process):
    def __init__(self, game_capture: mp.Process, postgres_config: Dict):
        super().__init__()
        self._game_capture = game_capture
        self._database_state_logger = DatabaseStateInterface(postgres_config)
        self.__setup_processes_shared_memory()

    def run(self):
        """
        Called on DatabaseStateLogger.start()
        """
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while self.is_running:
            state = self._game_capture.state_bytes
            self._database_state_logger.log_state(state)

    @property
    def is_running(self) -> bool:
        """
        Checks if the database logging process is running

        :return: True if the database logging process is running, false if it is not
        :rtype: bool
        """
        with self._is_running.get_lock():
            is_running = self._is_running.value
        return is_running

    @is_running.setter
    def is_running(self, is_running: bool):
        """
        Sets whether the database logging processes is running or noe

        :is_running: True if the database logging process is running, false if it is not
        :type is_running: bool
        """
        with self._is_running.get_lock():
            self._is_running.value = is_running

    def stop(self):
        """
        Stops the evaluation process
        """
        self.is_running = False

    def __setup_processes_shared_memory(self):
        self._is_running = mp.Value("i", True)


class DatabaseStateInterface(PostgresConnector):
    def __init__(self, postgres_config: Dict):
        super().__init__(postgres_config)
        self._maybe_create_database_table()
        self._insert_sql = get_insert_row_sql(self._table_name)
        self._previous_timestamp = 0
        self._total_previous_lap_times = 0

    def _maybe_create_database_table(self):
        if self._table_name is None:
            self._table_name = make_run_name()
        init_table_in_database(session=self._session, table_name=self._table_name)

    def log_state(self, state: bytes):
        state = state_bytes_to_dict(state)
        self._format_dictionary(state)
        self._update_timestamps(state)
        self._add_cumulative_time(state)
        python_types_state = convert_numpy_types(state)
        logger.info(python_types_state)
        self._insert_dict(python_types_state)

    def _format_dictionary(self, state: Dict):
        # Avoid using current_time, which is a protected phrase in SQL
        state["current_laptime"] = state.pop("current_time")

    def _update_timestamps(self, state: Dict):
        if self._previous_timestamp > state["i_current_time"]:
            self._total_previous_lap_times += state["i_last_time"]
            self._previous_timestamp = 0
        self._previous_timestamp = state["i_current_time"]

    def _add_cumulative_time(self, state: Dict):
        state["i_total_time"] = state["i_current_time"] + self._total_previous_lap_times

    def _insert_dict(self, data: Dict):
        with self._session.cursor() as cursor:
            try:
                cursor.execute(self._insert_sql, data)
                self._session.commit()
            except Exception as e:
                logger.error(f"Error inserting data: {e}")
                self._session.rollback()


def make_run_name() -> str:
    return "table" + datetime.now().strftime("%Y%m%d%H%M%S")


def init_table_in_database(session: psycopg.Connection, table_name: str):
    with session.cursor() as cursor:
        try:
            create_sql = get_create_table_sql(table_name)
            cursor.execute(create_sql)
            session.commit()
            logger.success(f'Made table in database "{table_name}"')
            return True
        except psycopg.errors.DuplicateTable as e:
            logger.warning(f"{e}, we'll just use the same table")
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            session.rollback()

    return None


def convert_numpy_types(data):
    converted_data = {
        k: NUMPY_TO_PYTHON_DTYPES.get(type(v), partial(lambda x: x))(v)
        for k, v in data.items()
    }
    cleaned_data = {
        k: replace_infinity(remove_null_characters(v))
        for k, v in converted_data.items()
    }
    return cleaned_data


def remove_null_characters(value):
    if isinstance(value, str):
        return value.replace("\u0000", "")
    return value


def replace_infinity(value):
    if isinstance(value, float) and (value == float("inf") or value == float("-inf")):
        return None
    return value
