from typing import Dict

from .base import AgentMonitor


class RestartMonitor(AgentMonitor):
    def _is_monitored_condition_met(self, observation: Dict) -> bool:
        return self._interface.restart_condition(observation)

    def _get_exhaustion_message(self) -> str:
        """
        Return the message to be logged on exhaustion of monitor patience
        """
        message = "Agent has met the restart condition "
        message += f"{self._n_consecutive_failures} times. Session Restarting..."
        return message
