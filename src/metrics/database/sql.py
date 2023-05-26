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


def get_select_sql(table_name: str, column_names: List[str]) -> str:
    sql = "SELECT "
    for column_name in column_names:
        sql += column_name + ", "
    sql = sql[:-2] + f" FROM {table_name}"
    return sql


def get_max_sql(table_name: str, column_names: List[str]) -> str:
    sql = "SELECT MAX("
    for column_name in column_names:
        sql += column_name + ", "
    sql = sql[:-2] + f") FROM {table_name}"
    return sql


def get_select_interval_max_sql(
    table_name: str,
    column_names: List[str],
    interval_column_name: str,
    interval: List[float],
    lap: int,
) -> str:
    sql = get_max_sql(table_name, column_names)
    sql += f" WHERE completed_laps={lap} AND {interval_column_name}"
    sql += f" BETWEEN {interval[0]} AND {interval[1]}"
    return sql


# Example time weighted average SQL query
"""
WITH setup AS (
    SELECT lag(temperature) OVER (PARTITION BY freezer_id ORDER BY ts) as prev_temp, 
        extract('epoch' FROM ts) as ts_e, 
        extract('epoch' FROM lag(ts) OVER (PARTITION BY freezer_id ORDER BY ts)) as prev_ts_e, 
        * 
    FROM  freezer_temps), 
nextstep AS (
    SELECT CASE WHEN prev_temp is NULL THEN NULL 
        ELSE (prev_temp + temperature) / 2 * (ts_e - prev_ts_e) END as weighted_sum, 
        * 
    FROM setup)
SELECT freezer_id,
    avg(temperature), -- the regular average
    sum(weighted_sum) / (max(ts_e) - min(ts_e)) as time_weighted_average 
"""
