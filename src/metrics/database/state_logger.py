from datetime import datetime
from functools import partial

import numpy as np
import psycopg
from loguru import logger

from src.utils.load import state_bytes_to_dict
from src.metrics.database.postgres import PostgresConnector
from src.metrics.database.sql import get_insert_row_sql, get_create_table_sql

NUMPY_TO_PYTHON_DTYPES = {
    np.int32: int,
    np.int64: int,
    np.float32: float,
    np.float64: float,
}


class DatabaseStateLogger(PostgresConnector):
    def __init__(
        self,
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="0.0.0.0",
        port="5432",
        table_name=None,
    ):
        super().__init__(dbname, user, password, host, port, table_name)
        self._maybe_create_database_table()
        self._insert_sql = get_insert_row_sql(self._table_name)

    def _maybe_create_database_table(self):
        if self._table_name is None:
            self._table_name = make_run_name()
        init_table_in_database(session=self._session, table_name=self._table_name)

    def log_state(self, state: bytes):
        state = state_bytes_to_dict(state)
        # Avoid using current_time, which is a protected phrase in SQL
        state["current_laptime"] = state.pop("current_time")
        python_types_state = convert_numpy_types(state)
        self._insert_dict(python_types_state)

    def _insert_dict(self, data):
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
