import pyarrow as pa
from src.game_capture.state.shared_memory.ac.combined import COMBINED_CTYPES

CTYPES_TO_POSTGRES = {
    "c_int": "INTEGER",
    "c_float": "REAL",
    "c_wchar_Array_15": "VARCHAR(15)",
    "c_wchar_Array_33": "VARCHAR(33)",
}

POSTGRES_DATA_SCHEMA = [
    (field[0], CTYPES_TO_POSTGRES[field[1].__name__]) for field in COMBINED_CTYPES
]
