from collections import defaultdict
from dataclasses import dataclass
from functools import wraps
from typing import List
import time

from loguru import logger
import numpy as np

LOG_EVERY_N = 5000
N_EXECUTIONS_TO_TRACK = 10000

class FunctionStats:
    def __init__(self):
        self._execution_times = -1.0 * np.ones(N_EXECUTIONS_TO_TRACK, dtype=np.float32)
        self._n_tracked = 0
    
    def add_execution_times(self, time_ms: float):
        index = self._n_tracked % N_EXECUTIONS_TO_TRACK
        self._execution_times[index] = time_ms
        self._n_tracked += 1
    
    def average_execution_time(self) -> float:
        return np.mean(self.execution_times)

    
    def standard_deviation_of_execution_time(self) -> float:
        return np.std(self.execution_times)
    
    @property
    def execution_times(self) -> np.array:
        if self._n_tracked < N_EXECUTIONS_TO_TRACK:
            execution_times = self._execution_times[self._execution_times > 0]
        else:
            execution_times = self._execution_times
        return execution_times 



class SystemMonitor:
    def __init__(self):
        self.runtimes = defaultdict(FunctionStats)
        self._n_iterations = 0

    def add_function_runtime(self, function_name: str, runtime: float):
        self.runtimes[function_name].add_execution_times(runtime)
    
    def maybe_log_function_itterations_per_second(self):
        if self._is_logging_interval:
            System_Monitor._log_function_itterations_per_second()
        self._n_iterations += 1

    @property
    def _is_logging_interval(self) -> bool:
        return self._n_iterations % LOG_EVERY_N == 0

    def log_function_runtimes_times(self):
        for key in self.runtimes.keys():
            function_stats = self.runtimes[key]
            average_runtime = function_stats.average_execution_time()
            std_dev = function_stats.standard_deviation_of_execution_time()
            logger.info(f"{key} runs: {average_runtime:.2f} ± {std_dev:.2f} ms")

    def _log_function_itterations_per_second(self):
        for key in self.runtimes.keys():
            its_per_s = 1000.0 / self.runtimes[key].average_execution_time()
            logger.info(f"{key} - Processing frequency: {its_per_s:.2f} it/s")


System_Monitor = SystemMonitor()


def track_runtime(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        t1 = time.time()
        result = function(*args, **kwargs)
        t2 = time.time()
        name = f"{function.__module__}.{function.__name__}"
        System_Monitor.add_function_runtime(name, (t2 - t1) * 10e3)
        return result

    return wrapper
