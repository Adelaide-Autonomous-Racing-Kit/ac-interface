import os
from pathlib import Path
import subprocess

from aci.config.constants import PROTON_AC_APPID_FILE_PATH
from .base import AssettoCorsaLauncher

PROJECT_PATH = Path(os.path.dirname(__file__)).parents[0]


class ProtonLauncher(AssettoCorsaLauncher):
    def _launch_assetto_corsa(self):
        """
        Launches AC
        """
        run_script_path = Path(PROJECT_PATH, "scripts/run_ac.sh")
        subprocess.Popen(
            ["bash", str(run_script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def _shutdown_assetto_corsa(self):
        """
        Shutdown AC
        """
        subprocess.run(["pkill", "-f", "acs.exe"])

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

    def _setup_steam_appid_path(self):
        """
        Add path to steam app id file for Assetto Corsa
        """
        self._steam_appid_file_path = PROTON_AC_APPID_FILE_PATH


class DockerProtonLauncher(AssettoCorsaLauncher):
    def _launch_assetto_corsa(self):
        """
        Launches AC
        """
        with open("/execution_pipes/aci_execution_pipe", "w") as f:
            f.write("proton_launch_ac\n")

    def _shutdown_assetto_corsa(self):
        """
        Shutdown AC
        """
        with open("/execution_pipes/aci_execution_pipe", "w") as f:
            f.write("proton_shutdown_ac\n")

    def _launch_sate_server(self):
        """
        Launch state server
        """
        # Proton will launch state server via steam launch options

    def _shutdown_state_server(self):
        """
        Shutdown state server
        """
        with open("/execution_pipes/aci_execution_pipe", "w") as f:
            f.write("proton_shutdown_server\n")
