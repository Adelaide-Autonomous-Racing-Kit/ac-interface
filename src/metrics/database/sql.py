import ctypes

from src.game_capture.state.shared_memory.ac.combined import COMBINED_DATA_TYPES

NUMPY_TO_SQL_DTYPES = {
    ctypes.c_int: "int4",
    ctypes.c_float: "float4",
    "V30": "text",
    "V68": "text",
}


def get_create_table_sql(table_name: str) -> str:
    sql = f"CREATE TABLE {table_name} (\n"
    sql += "id SERIAL PRIMARY KEY,\n"
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


"SELECT acc_status FROM {filled_database_logger._table_name}"
