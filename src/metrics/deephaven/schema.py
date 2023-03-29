import pyarrow as pa

from src.game_capture.state.shared_memory.ac.combined import COMBINED_CTYPES

CTYPES_TO_PYARROW = {
    "c_int": pa.int32,
    "c_float": pa.float32,
    "c_wchar_Array_15": pa.string,
    "c_wchar_Array_33": pa.string,
}

PYARROW_DATA_SCHEMA = pa.schema(
    [(field[0], CTYPES_TO_PYARROW[field[1].__name__]()) for field in COMBINED_CTYPES]
)
