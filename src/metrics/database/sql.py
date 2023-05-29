import ctypes
from typing import List

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
    sql += "i_total_time BIGSERIAL,\n"
    for name, dtype in COMBINED_DATA_TYPES:
        sql_dtype = NUMPY_TO_SQL_DTYPES[dtype]
        if name == "current_time":
            name = "current_laptime"
        sql += f"{name} {sql_dtype},\n"
    return modify_sql_ending(sql)


def get_insert_row_sql(table_name: str) -> str:
    sql_1 = f"INSERT INTO {table_name} (i_total_time, "
    sql_2 = "VALUES (%(i_total_time)s, "
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


def get_select_sql(table_name: str, column_names: List[str]) -> str:
    sql = "SELECT "
    for column_name in column_names:
        sql += column_name + ", "
    sql = sql[:-2] + f" FROM {table_name}"
    return sql


def get_max_sql(table_name: str, column_name: str) -> str:
    sql = f"SELECT MAX({column_name}) FROM {table_name}"
    return sql


def get_select_interval_max_sql(
    interval: List[float],
    interval_column_name: str,
    table_name: str,
    column_name: List[str],
) -> str:
    sql = get_max_sql(table_name, column_name)
    sql += f" WHERE completed_laps=0 AND {interval_column_name}"
    sql += f" BETWEEN {interval[0]} AND {interval[1]}"
    return sql


# Example time weighted average SQL query

"""
WITH setup AS (
    SELECT LAG(i_total_time) OVER (ORDER BY id) as i_previous_timestamp, LAG(throttle) OVER (ORDER BY id) as previous_reading, * FROM tablepg5_vqas),
nextstep AS (
    SELECT CASE WHEN previous_reading is NULL THEN NULL 
        ELSE (previous_reading + throttle) / 2 * (i_total_time - i_previous_timestamp) END as weighted_sum, 
        * 
    FROM setup)
SELECT sum(weighted_sum) / (max(i_total_time) - min(i_total_time)) as time_weighted_average FROM nextstep
"""
