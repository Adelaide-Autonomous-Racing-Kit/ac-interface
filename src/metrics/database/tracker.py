import abc
from typing import Dict, List

from src.metrics.database.sql import get_select_interval_max_sql


class Tracker(abc.ABC):
    def __init__(
        self,
        interval: List,
        interval_column_name: str,
        table_name: str,
        tracked_column_name: str,
    ):
        self._interval = interval
        self._interval_column_name = interval_column_name
        self._table_name = table_name
        self._tracked_column_name = tracked_column_name
        self.current_lap = 0

    @abc.abstractmethod
    def get_sql_query(self) -> Dict:
        """
        Implements logic for constructing the sql query that will be executed by
            monitor.Monitor to track a given metric.

        :return: Postgres SQL query with variables to be bound
        :rtype: Dict["query": str, "to_bind": Dict['name': value]]
        """
        pass


class IntervalMaxTracker(Tracker):
    def __init__(
        self,
        interval: List,
        interval_column_name: str,
        table_name: str,
        tracked_column_name: str,
    ):
        super().__init__(
            interval,
            interval_column_name,
            table_name,
            tracked_column_name,
        )
        self._sql_query = get_select_interval_max_sql(
            self._interval,
            self._interval_column_name,
            self._table_name,
            self._tracked_column_name,
        )

    def __repr__(self) -> str:
        string = f"A tracker configured to get the maximum value of "
        string += f"{self._tracked_column_name} between {self._interval[0]} and "
        string += f"{self._interval[1]} of {self._interval_column_name}"

    def get_sql_query(self) -> Dict:
        query = {
            "query": self._sql_query,
            "to_bind": {"lap": self.current_lap},
        }
        return query
