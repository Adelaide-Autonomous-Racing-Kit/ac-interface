import os
from pathlib import Path
import subprocess
import time
from typing import Dict


from aci.config.constants import AC_STEAM_PATH
from acs.client import StateClient
from aci.utils.os import move_application_window
from .base import AssettoCorsaLauncher


class CrossOverLauncher(AssettoCorsaLauncher):
    def __init__(self, config: Dict):
        super().__init__(config)
        self._p_state_server = None

    def _launch_assetto_corsa(self):
        """
        Launch AC
        """
        original_dir = Path.cwd()
        os.chdir(AC_STEAM_PATH)
        subprocess.Popen(
            [
                "/opt/cxoffice/bin/wine",
                "--bottle",
                "Assetto_Corsa",
                "--cx-app",
                "acs.exe",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        os.chdir(original_dir)

    def _move_assetto_corsa_window(self):
        location, resolution = self._window_location, self._window_resolution
        move_application_window("AC", resolution, location)

    def _shutdown_assetto_corsa(self):
        """
        Shutdown AC
        """
        subprocess.run(["pkill", "acs.exe"])

    def _launch_sate_server(self):
        """
        Launch state server
        """
        self._try_until_state_server_is_launched()

    def _try_until_state_server_is_launched(self):
        """
        Continues to start state server subprocesses until a client is able to
            bind to one
        """
        is_running = self._test_connection_to_server()
        while not is_running:
            self._maybe_start_state_server()
            time.sleep(2)
            is_running = self._test_connection_to_server()
            if not is_running:
                self._shutdown_state_server()

    def _maybe_start_state_server(self):
        p_state_server = subprocess.Popen(
            [
                "/opt/cxoffice/bin/wine",
                "--bottle",
                "Assetto_Corsa",
                "--cx-app",
                "cmd.exe",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        p_state_server.stdin.write("python -m acs.server\n".encode())
        self._p_state_server = p_state_server

    def _shutdown_state_server(self):
        """
        Shutdown state server
        """
        if self._p_state_server is not None:
            self._p_state_server.terminate()
