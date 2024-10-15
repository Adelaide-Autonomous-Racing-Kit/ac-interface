from collections import defaultdict
from functools import wraps
import time

from loguru import logger
import numpy as np

LOG_EVERY_N = 5000
N_EXECUTIONS_TO_TRACK = 1000


class FunctionStats:
    def __init__(self):
        self._execution_times = -1.0 * np.ones(N_EXECUTIONS_TO_TRACK, dtype=np.float32)
        self._n_tracked = 0
        self._start_time = time.time_ns()

    def add_execution_times(self, time_ms: float):
        index = self._n_tracked % N_EXECUTIONS_TO_TRACK
        self._execution_times[index] = time_ms
        self._n_tracked += 1

    @property
    def average_execution_time(self) -> float:
        return np.mean(self.execution_times)

    @property
    def standard_deviation_of_execution_time(self) -> float:
        return np.std(self.execution_times)

    @property
    def itteration_per_second(self) -> float:
        time_elapsed = (time.time_ns() - self._start_time) * 1e-9
        return self._n_tracked / time_elapsed

    @property
    def execution_times(self) -> np.array:
        if self._n_tracked < N_EXECUTIONS_TO_TRACK:
            execution_times = self._execution_times[self._execution_times > 0]
        else:
            execution_times = self._execution_times
        return execution_times


class SystemMonitor:
    def __init__(self, log_every_n: int):
        self.runtimes = defaultdict(FunctionStats)
        self._n_iterations = 0
        self._log_every_n = log_every_n

    def add_function_runtime(self, function_name: str, runtime: float):
        self.runtimes[function_name].add_execution_times(runtime)

    def maybe_log_function_itterations_per_second(self):
        if self._is_logging_interval:
            self._log_function_itterations_per_second()
        self._n_iterations += 1

    @property
    def _is_logging_interval(self) -> bool:
        return self._n_iterations % self._log_every_n == 0

    def log_function_runtimes_times(self):
        for key in self.runtimes.keys():
            function_stats = self.runtimes[key]
            average_runtime = function_stats.average_execution_time
            std_dev = function_stats.standard_deviation_of_execution_time
            logger.info(f"{key} runs: {average_runtime:.2f} ± {std_dev:.2f} ms")

    def _log_function_itterations_per_second(self):
        for key in self.runtimes.keys():
            function_stats = self.runtimes[key]
            average_runtime = function_stats.average_execution_time
            std_dev = function_stats.standard_deviation_of_execution_time
            observed_it_per_s = function_stats.itteration_per_second
            message = f"{key}: \n"
            message += f"Average runtime: {average_runtime:.2f} ± {std_dev:.2f} ms\n"
            message += f"Theoretical max: {(1000.0 / average_runtime):.2f} it/s\n"
            message += f"Observed: {observed_it_per_s:.2f} it/s"
            logger.debug(message)


System_Monitor = SystemMonitor(LOG_EVERY_N)
from typing import Callable


def track_runtime(system_monitor: SystemMonitor):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            t1 = time.time_ns()
            result = function(*args, **kwargs)
            t2 = time.time_ns()
            name = f"{function.__module__}.{function.__name__}"
            system_monitor.add_function_runtime(name, (t2 - t1) * 1e-6)
            return result

        return wrapper

    return decorator
