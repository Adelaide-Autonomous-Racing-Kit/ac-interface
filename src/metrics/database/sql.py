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
    sql = f"CREATE UNLOGGED TABLE {table_name} (\n"
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


def get_interval_max_sql(
    interval: List[float],
    interval_column_name: str,
    table_name: str,
    column_name: List[str],
) -> str:
    sql = get_max_sql(table_name, column_name)
    sql += f" WHERE completed_laps=%(lap)s AND {interval_column_name}"
    sql += f" BETWEEN {interval[0]} AND {interval[1]}"
    return sql


def get_max_sql(table_name: str, column_name: str) -> str:
    sql = f"SELECT MAX({column_name}) FROM {table_name}"
    return sql


def get_interval_min_sql(
    interval: List[float],
    interval_column_name: str,
    table_name: str,
    column_name: List[str],
) -> str:
    sql = get_min_sql(table_name, column_name)
    sql += f" WHERE completed_laps=%(lap)s AND {interval_column_name}"
    sql += f" BETWEEN {interval[0]} AND {interval[1]}"
    return sql


def get_min_sql(table_name: str, column_name: str) -> str:
    sql = f"SELECT MIN({column_name}) FROM {table_name}"
    return sql


def get_time_weighted_average_sql(
    interval: List[float],
    interval_column_name: str,
    table_name: str,
    column_name: List[str],
):
    sql = (
        f"WITH SETUP AS ("
        "SELECT LAG(i_total_time) OVER (ORDER BY i_total_time) AS previous_timestamp, "
        f"LAG({column_name}) OVER (ORDER BY i_total_time) AS previous_reading, "
        f"{column_name}, i_total_time "
        f"FROM {table_name} WHERE completed_laps=%(lap)s AND {interval_column_name} "
        f"BETWEEN {interval[0]} AND {interval[1]}"
        "),"
        "nextstep AS ("
        "SELECT CASE WHEN previous_reading is NULL THEN NULL "
        f"ELSE (previous_reading + {column_name}) / 2 * "
        "(i_total_time - previous_timestamp) END AS weighted_sum, i_total_time "
        "FROM setup"
        ")"
        "SELECT SUM(weighted_sum) / (MAX(i_total_time) - MIN(i_total_time)) AS "
        "time_weighted_average FROM nextstep"
    )
    return sql
