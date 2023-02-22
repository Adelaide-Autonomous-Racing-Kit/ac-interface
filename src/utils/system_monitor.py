from collections import defaultdict
from functools import wraps
import time

from loguru import logger
import numpy as np


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


class SystemMonitor:
    def __init__(self):
        self.runtimes = defaultdict(list)

    def add_function_runtime(self, function_name: str, runtime: float):
        self.runtimes[function_name].append(runtime)

    def average_runtime(self, function_name: str) -> float:
        return np.mean(self.runtimes[function_name])

    def standard_deviation_of_runtime(self, function_name: str) -> float:
        return np.std(self.runtimes[function_name])

    def log_function_runtimes_times(self):
        for key in self.runtimes.keys():
            average_runtime = self.average_runtime(key)
            std_dev = self.standard_deviation_of_runtime(key)
            logger.info(f"{key} runs: {average_runtime:.2f} ± {std_dev:.2f} ms")


System_Monitor = SystemMonitor()
