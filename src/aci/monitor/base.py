from __future__ import annotations
import abc
from typing import Dict

from loguru import logger


class AgentMonitor(abc.ABC):
    def __init__(self, config: Dict, interface: AssettoCorsaInterface):
        self._setup(config, interface)

    def _setup(self, config: Dict, interface: AssettoCorsaInterface):
        self._interface = interface
        self._n_steps_between_checks = config.get("check_every_n", -1)
        self._n_max_consecutive_failures = config.get("max_consecutive_failures", 0)
        self.reset()

    def reset(self):
        self._n_steps_since_last_check = 0
        self._n_consecutive_failures = 0

    def is_triggered(self, observation: Dict) -> bool:
        if self._is_monitor_disabled:
            return False

        if self._is_unmonitored_interval:
            self._n_steps_since_last_check += 1
            return False

        self._check_monitored_condition(observation)
        return self._is_monitor_triggered

    @property
    def _is_monitor_disabled(self) -> bool:
        return self._n_steps_between_checks < 0

    @property
    def _is_unmonitored_interval(self) -> bool:
        return self._n_steps_between_checks > self._n_steps_since_last_check

    def _check_monitored_condition(self, observation: Dict):
        if self._is_monitored_condition_met(observation):
            self._n_consecutive_failures += 1
        else:
            self._n_consecutive_failures = 0
        self._n_steps_since_last_check = 0

    @abc.abstractmethod
    def _is_monitored_condition_met(self, observation: Dict) -> bool:
        """
        Return the value produced by the user defined abstract condition function
            on the interface class here. Either "termination_condition" or
            "restart_condition"
        """
        pass

    @property
    def _is_monitor_triggered(self) -> bool:
        if self._is_patience_exhausted:
            self._log_exhaustion()
            return True
        return False

    @property
    def _is_patience_exhausted(self) -> bool:
        return self._n_consecutive_failures >= self._n_max_consecutive_failures

    def _log_exhaustion(self):
        logger.error(self._get_exhaustion_message())

    @abc.abstractmethod
    def _get_exhaustion_message(self) -> str:
        """
        Return the message to be logged on exhaustion of monitor patience
        """
        pass
