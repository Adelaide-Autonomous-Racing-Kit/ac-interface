from typing import Dict

from .base import AgentMonitor


class TerminationMonitor(AgentMonitor):
    def _is_monitored_condition_met(self, observation: Dict) -> bool:
        return self._interface.termination_condition(observation)

    def _get_exhaustion_message(self) -> str:
        """
        Return the message to be logged on exhaustion of monitor patience
        """
        message = "Agent has met the termination condition "
        message += f"{self._n_consecutive_failures} times. Terminating execution"
        return message
