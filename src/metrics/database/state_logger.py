import ctypes
from datetime import datetime
from functools import partial

from loguru import logger
import numpy as np
import psycopg
from psycopg.types.json import Jsonb
from src.utils.load import state_bytes_to_dict
from src.game_capture.state.shared_memory.ac.combined import COMBINED_DATA_TYPES

NUMPY_TO_SQL_DTYPES = {
    ctypes.c_int: "int4",
    ctypes.c_float: "float4",
    "V30": "text",
    "V68": "text",
}
NUMPY_TO_PYTHON_DTYPES = {
    np.int32: int,
    np.int64: int,
    np.float32: float,
    np.float64: float,
}


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


def get_create_table_sql(table_name: str) -> str:
    sql = f"CREATE TABLE {table_name} (\n"
    for name, dtype in COMBINED_DATA_TYPES:
        sql_dtype = NUMPY_TO_SQL_DTYPES[dtype]
        if name == "current_time":
            name = "current_laptime"
        sql += f"{name} {sql_dtype},\n"
    return modify_sql_ending(sql)


def get_insert_row_sql(table_name: str) -> str:
    sql_1 = f"INSERT INTO {table_name} ("
    sql_2 = "VALUES ("
    for name, _ in COMBINED_DATA_TYPES:
        if name == "current_time":
            name = "current_laptime"
        sql_1 += f"{name}, "
        sql_2 += f"%({name})s, "
    sql_1 = modify_sql_ending(sql_1)
    sql_2 = modify_sql_ending(sql_2)
    return " ".join([sql_1, sql_2])


def modify_sql_ending(string: str) -> str:
    return string[:-2] + ")"


class DatabaseStateLogger:
    def __init__(
        self,
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="0.0.0.0",
        port="5432",
        table_name=None,
    ):
        self._session, self.table_name = self._setup_database_session(
            dbname, user, password, host, port, table_name
        )
        self._insert_sql = get_insert_row_sql(self.table_name)

    @staticmethod
    def _setup_database_session(
        dbname, user, password, host, port, table_name
    ) -> psycopg.Connection:
        session = psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        logger.success("Connected to Database")

        if not table_name:
            table_name = DatabaseStateLogger._make_run_name()

        DatabaseStateLogger._init_table_in_database(
            session=session, table_name=table_name
        )

        return session, table_name

    @staticmethod
    def _init_table_in_database(session: psycopg.Connection, table_name: str):
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

    @staticmethod
    def _make_run_name() -> str:
        return "table" + datetime.now().strftime("%Y%m%d%H%M%S")

    def log_state(self, state: bytes):
        state = state_bytes_to_dict(state)
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

    def close(self):
        self._session.close()

    def get_all_data(self):
        with self._session.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name}")
            rows = cursor.fetchall()

        return rows


import tempfile

if __name__ == "__main__":
    table_name = "table" + next(tempfile._get_candidate_names())
    get_insert_row_sql(table_name)
    DatabaseStateLogger(table_name=table_name)
