import abc
from typing import Dict, List

from aci.metrics.database.sql import (
    get_interval_max_sql,
    get_interval_min_sql,
    get_time_weighted_average_sql,
)


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
        self._setup()

    @abc.abstractmethod
    def _setup(self):
        """
        Implements any setup logic required by the base class.
        """
        pass

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
    def _setup(self):
        self._sql_query = get_interval_max_sql(
            self._interval,
            self._interval_column_name,
            self._table_name,
            self._tracked_column_name,
        )

    def __repr__(self) -> str:
        string = "A tracker configured to get the maximum value of "
        string += f"{self._tracked_column_name} between {self._interval[0]} and "
        string += f"{self._interval[1]} of {self._interval_column_name}"

    def get_sql_query(self) -> Dict:
        query = {
            "query": self._sql_query,
            "to_bind": {"lap": self.current_lap},
        }
        return query


class IntervalMinTracker(Tracker):
    def _setup(self):
        self._sql_query = get_interval_min_sql(
            self._interval,
            self._interval_column_name,
            self._table_name,
            self._tracked_column_name,
        )

    def __repr__(self) -> str:
        string = "A tracker configured to get the minimum value of "
        string += f"{self._tracked_column_name} between {self._interval[0]} and "
        string += f"{self._interval[1]} of {self._interval_column_name}"

    def get_sql_query(self) -> Dict:
        query = {
            "query": self._sql_query,
            "to_bind": {"lap": self.current_lap},
        }
        return query


class AverageIntervalTracker(Tracker):
    def _setup(self):
        self._sql_query = get_time_weighted_average_sql(
            self._interval,
            self._interval_column_name,
            self._table_name,
            self._tracked_column_name,
        )

    def __repr__(self) -> str:
        string = "A tracker configured to get the average value of "
        string += f"{self._tracked_column_name} between {self._interval[0]} and "
        string += f"{self._interval[1]} of {self._interval_column_name}"

    def get_sql_query(self) -> Dict:
        query = {
            "query": self._sql_query,
            "to_bind": {"lap": self.current_lap},
        }
        return query


TRACKER_TYPES = {
    "maximum_interval": IntervalMaxTracker,
    "minimum_interval": IntervalMinTracker,
    "average_interval": AverageIntervalTracker,
}
