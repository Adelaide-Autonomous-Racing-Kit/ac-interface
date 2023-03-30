from datetime import datetime
import os
import time
from typing import Dict

from loguru import logger
import pyarrow as pa
from pydeephaven import DHError, Session, Table
from src.metrics.deephaven.schema import PYARROW_DATA_SCHEMA
from src.utils.load import state_bytes_to_dict
from tqdm import tqdm


class DeephavenStateLogger:
    def __init__(self):
        self._setup_deephaven_session()

    def _setup_deephaven_session(self):
        try:
            logger.info("Connecting to Deephaven...")
            self._session = Session()
            logger.success("Connected to Deephaven")
        except DHError as e:
            logger.info(f"DHError from deephaven: {e}")
            logger.error(
                "Deephaven error when connecting to session, is the docker compose image active? check with `docker container ls`, you can also try to start it with `docker compose up -d`."
            )
            exit(1)
        except Exception as e:
            print("Unknown error")
            print(e)

        self._primary_table = self._session.input_table(PYARROW_DATA_SCHEMA)
        self._session.bind_table(self._get_run_name(), self._primary_table)

    # TODO: Descriptive, unique, table name
    def _get_run_name(self) -> str:
        return datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    def log_state(self, state: bytes):
        state = load_state_as_dict(state)
        temporary_table = self._create_temporary_deephaven_table(state)
        self._primary_table.add(temporary_table)

    def _create_temporary_deephaven_table(self, state: Dict) -> Table:
        pa_table = pa.Table.from_pydict(state, schema=PYARROW_DATA_SCHEMA)
        return self._session.import_table(pa_table)


def load_state_as_dict(state: bytes) -> Dict:
    state = state_bytes_to_dict(state)
    return {key: [value] for key, value in state.items()}


RECORDING_PATH = "../recordings/monza_audi_r8_lms_1/"


def main():
    deephaven_logger = DeephavenStateLogger()

    records = [
        os.path.join(RECORDING_PATH, name)
        for name in os.listdir(RECORDING_PATH)
        if name[-3:] == "bin"
    ]
    binary_records = []
    for record in records:
        with open(record, "rb") as file:
            binary_record = file.read()
        binary_records.append(binary_record)

    start = time.time()
    for binary_record in tqdm(binary_records):
        deephaven_logger.push_state_to_deephaven(binary_record)
    elapsed = time.time() - start
    logger.info(f"{elapsed}s")


if __name__ == "__main__":
    main()
