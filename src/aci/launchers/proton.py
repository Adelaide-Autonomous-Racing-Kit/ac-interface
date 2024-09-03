import subprocess

from aci.utils.os import move_application_window
from loguru import logger

from .base import AssettoCorsaLauncher


class ProtonLauncher(AssettoCorsaLauncher):
    def _launch_assetto_corsa(self):
        """
        Launches AC
        """
        subprocess.Popen(
            ["bash", "scripts/run_ac.sh"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def _move_assetto_corsa_window(self):
        location, resolution = self._window_location, self._window_resolution
        move_application_window("AC", resolution, location)

    def _shutdown_assetto_corsa(self):
        """
        Shutdown AC
        """
        subprocess.run(["pkill", "AssettoCorsa.ex"])

    def _launch_sate_server(self):
        """
        Launch state server
        """
        # Proton will launch state server via steam launch options
        pass

    def _shutdown_state_server(self):
        """
        Shutdown state server
        """
        subprocess.run(["pkill", "ac-state.exe"])
