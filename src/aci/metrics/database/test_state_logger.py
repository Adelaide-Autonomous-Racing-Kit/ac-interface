import pathlib
import tempfile
import time

import psycopg
import pytest
from aci.metrics.database.state_logger import DatabaseStateInterface


def cleanup_test(session: psycopg.Connection, table_name: str):
    with session.cursor() as cur:
        # Drop the table
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        session.commit()

        # Check if the table was indeed deleted
        cur.execute(
            f"SELECT * FROM information_schema.tables WHERE table_name = '{table_name}'"
        )
        exists = cur.fetchone()

    assert not exists, f"{exists=}"
    session.close()


def read_binary_file(path: pathlib.Path) -> bytes:
    with open(path, "rb") as f:
        binary = f.read()
    return binary


@pytest.fixture
def database_logger():
    postgres_config = {
        "dbname": "postgres",
        "user": "postgres",
        "password": "postgres",
        "host": "0.0.0.0",
        "port": "5432",
        "table_name": "table" + next(tempfile._get_candidate_names()),
    }
    logger = DatabaseStateInterface(postgres_config)
    yield logger
    cleanup_test(logger._session, logger._table_name)


@pytest.fixture
def binary_files(
    test_recordings_dir=pathlib.Path("aci/metrics/database/test_recording/"),
    num_files_to_test: int = 60,
):
    binary_filepaths = test_recordings_dir.glob("*.bin")
    return list(map(read_binary_file, list(binary_filepaths)[:num_files_to_test]))


@pytest.fixture
def filled_database_logger(database_logger, binary_files):
    assert len(binary_files) > 1

    for binary_file in binary_files:
        database_logger.log_state(binary_file)

    yield database_logger


@pytest.mark.io
def test_binary_records_can_read_fast_enough(database_logger, binary_files):
    """
    Test if binary records can be read faster than 60Hz realtime.
    """
    assert len(binary_files) > 1

    start = time.time()

    for binary_file in binary_files:
        database_logger.log_state(binary_file)

    elapsed = time.time() - start
    assert elapsed < (
        len(binary_files) / 60
    ), f"{elapsed:0.2f} seconds needs to be faster than 60hz realtime"


@pytest.mark.io
def test_all_records_are_in_database(filled_database_logger, binary_files):
    """
    Test if all records are stored in the database.
    """
    with filled_database_logger._session.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {filled_database_logger._table_name}")
        rows = cursor.fetchall()

    assert len(rows) == len(binary_files)


@pytest.mark.io
def test_a_query_works_with_database(filled_database_logger, binary_files):
    """
    Test if a query can be executed successfully on the database.
    """
    with filled_database_logger._session.cursor() as cursor:
        cursor.execute(f"SELECT acc_status FROM {filled_database_logger._table_name}")
        rows = cursor.fetchall()

    assert len(rows) == len(binary_files)


if __name__ == "__main__":
    pytest
