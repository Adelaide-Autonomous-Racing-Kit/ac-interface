import os
import time

import pyarrow as pa
from loguru import logger
from pydeephaven import Session
from tqdm import tqdm

from src.utils.load import load_game_state
from src.utils.system_monitor import System_Monitor, track_runtime

RECORDING_PATH = "../recordings/monza_audi_r8_lms_1/"


@track_runtime
def make_pa_table(record):
    return pa.Table.from_pydict(record)


@track_runtime
def import_table(pa_table):
    return session.import_table(pa_table)


@track_runtime
def add_row(primary_table, tmp_table):
    primary_table.add(tmp_table)


records = [
    os.path.join(RECORDING_PATH, name)
    for name in os.listdir(RECORDING_PATH)
    if name[-3:] == "bin"
]
_records = []
records = map(load_game_state, records)
for record in records:
    for key in record.keys():
        record[key] = [record[key]]
    _records.append(record)

pa_table = pa.Table.from_pydict(_records[0])

session = Session()
pyarrow_schema = pa_table.schema
primary_table = session.input_table(pyarrow_schema)
session.bind_table("test", primary_table)


start = time.time()
for record in tqdm(_records):
    pa_table = make_pa_table(record)
    tmp_table = import_table(pa_table)
    add_row(primary_table, tmp_table)
elapsed = time.time() - start
logger.info(f"{elapsed}s")
session.close()
System_Monitor.log_function_runtimes_times()
