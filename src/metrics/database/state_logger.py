from datetime import datetime
import pathlib
import time

from loguru import logger
import numpy as np
import psycopg
from psycopg.types.json import Jsonb
from src.utils.load import state_bytes_to_dict


def convert_numpy_types(data):
    conversion_dict = {
        np.int32: int,
        np.int64: int,
        np.float32: float,
        np.float64: float,
    }

    converted_data = {
        k: conversion_dict.get(type(v), lambda x: x)(v) for k, v in data.items()
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


class DatabaseStateLogger:
    def __init__(self):
        self._session = self._setup_database_session()

    def _setup_database_session(self):
        try:
            self._session = psycopg.connect(
                dbname="postgres",
                user="postgres",
                password="postgres",
                host="0.0.0.0",
                port="5432",
            )
            logger.success("Connected to Database")
        except Exception as e:
            print("Unknown error", e)

        self.table_name = self._get_run_name()

        with self._session.cursor() as cursor:
            try:
                cursor.execute(f"create table {self.table_name} (data jsonb)")
                self._session.commit()
                logger.success(f'Made table in database "{self.table_name}"')
            except psycopg.errors.DuplicateTable as e:
                logger.warning(f"{e}, we'll just use the same table")
            except Exception as e:
                logger.error(f"Error creating table: {e}")
                self._session.rollback()

        self._insert_sql = f"insert into {self.table_name} (data) values (%s::jsonb)"

        return self._session

    def _get_run_name(self) -> str:
        return "table" + datetime.now().strftime("%Y%m%d%H%M%S")

    def log_state(self, state: bytes):
        state = state_bytes_to_dict(state)

        python_types_state = convert_numpy_types(state)

        self._insert_dict(python_types_state)

    def _insert_dict(self, data):
        with self._session.cursor() as cursor:
            try:
                cursor.execute(self._insert_sql, [Jsonb(data)])
                self._session.commit()
            except Exception as e:
                logger.error(f"Error inserting data: {e}")
                self._session.rollback()

    def _create_table_sql(self, tablename, columns):
        sql = f"CREATE TABLE {tablename} (\n"
        for column_name, sqltype in columns:
            sql += f"  {column_name} {sqltype},\n"
        sql = sql.rstrip(",\n") + "\n);\n"
        return sql

    def print_all_data(self):
        with self._session.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name}")
            rows = cursor.fetchall()

        return rows


RECORDING_PATH = "recordings/monza_audi_r8_lms_1/"


def main():
    binary_filepaths = pathlib.Path("src/metrics/database/test_recording/").glob(
        "*.bin"
    )

    def read_binary_file(path: pathlib.Path) -> bytes:
        with open(path, "rb") as f:
            binary = f.read()
        return binary

    binary_files = list(map(read_binary_file, list(binary_filepaths)[:60]))
    assert len(binary_files) == 60

    database_logger = DatabaseStateLogger()

    start = time.time()
    for binary_file in binary_files:
        database_logger.log_state(binary_file)

    elapsed = time.time() - start
    assert elapsed < 1, f"{elapsed:0.2f} seconds needs to be faster than 60hz realtime"
    print("done", elapsed)

    all_data = database_logger.print_all_data()
    assert len(all_data) == len(binary_files)

    start = time.time()
    with database_logger._session.cursor() as cursor:
        cursor.execute(
            f"SELECT CAST(data->>'acc_status' AS INTEGER) FROM {database_logger.table_name}"
        )

        rows = cursor.fetchall()
    elapsed = time.time() - start
    assert elapsed < 1, f"{elapsed:0.2f} seconds needs to be faster than 60hz realtime"
    print("done", elapsed)

    print(rows)


if __name__ == "__main__":
    main()
