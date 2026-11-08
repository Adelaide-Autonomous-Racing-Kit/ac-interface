from collections import deque
import os
import subprocess
from threading import Thread
import time
from typing import Dict

from Xlib import X, error
from aci.config.constants import GAME_NAME_TO_WINDOW_NAME, STEAM_APPID, crossover_paths
from aci.game_capture.video.get_window import (
    get_window_absolute_location,
    get_window_linux,
)
from aci.utils.data import Point
from acs.client import StateClient

from .base import AssettoCorsaLauncher

STATE_SERVER_STARTUP_TIMEOUT = 30


class CrossOverLauncher(AssettoCorsaLauncher):
    def __init__(self, config: Dict):
        capture = config["capture"]
        self._private = capture.get("private_display", False)
        self._direct = capture.get("images", {}).get("backend") == "game_frame"
        self._bottle = capture.get("crossover_bottle", "Assetto_Corsa")
        self._game_dir, _ = crossover_paths(config)
        self._p_game = None
        if self._private:
            if (
                (
                    self._bottle == "Assetto_Corsa"
                    and not (
                        os.environ.get("ACI_REUSE_DESKTOP_STEAM") == "1"
                        and os.environ.get("ACI_DISPLAY_PROVIDER") == "xvfb"
                    )
                )
                or not os.environ.get("ACI_PRIVATE_DISPLAY")
                or os.environ.get("DISPLAY") != os.environ["ACI_PRIVATE_DISPLAY"]
                or not self._direct
            ):
                raise RuntimeError(
                    "Private AC launch requires the headless supervisor and an authorized bottle"
                )
        super().__init__(config)
        self._p_state_server = None
        self._state_server_log = deque(maxlen=30)
        self._state_server_log_reader = None

    def _setup_window_location(self):
        if self._private:
            self._window_location = Point(0, 0)
        else:
            super()._setup_window_location()

    def _place_window_on_xvfb(self):
        window = get_window_linux(
            GAME_NAME_TO_WINDOW_NAME["linux"]["AC"], self._window_resolution
        )
        # Wine can restore coordinates from a larger desktop. On Xvfb there
        # is no window manager to bring that off-screen window into view.
        placement_error = error.CatchError()
        window.configure(x=0, y=0, stack_mode=X.Above, onerror=placement_error)
        window.set_input_focus(X.RevertToParent, X.CurrentTime, onerror=placement_error)
        if (
            get_window_absolute_location(window) != self._window_location
            or placement_error.get_error() is not None
        ):
            raise RuntimeError(
                "Could not place AC at the origin of the private display"
            )
        print(
            f"AC window {window.id:#x} placed on private display {os.environ['DISPLAY']}",
            flush=True,
        )

    def launch_assetto_corsa(self):
        if not self._direct:
            return super().launch_assetto_corsa()
        # The supervisor stages and restores the collection settings.
        if self._steam_appid_file_path.read_text().strip() != STEAM_APPID:
            raise RuntimeError("The CrossOver bottle needs a valid steam_appid.txt")
        self._launch_assetto_corsa()
        client = StateClient()
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if self._p_game.poll() is not None:
                    raise RuntimeError(
                        f"acs.exe exited ({self._p_game.returncode}); see Wine log"
                    )
                if not client.update_thread.is_alive():
                    raise RuntimeError(
                        "The owned telemetry server disconnected during startup"
                    )
                state = client._latest_state
                if state is not None and state["physics_packet_id"] > 500:
                    if (
                        self._private
                        and os.environ.get("ACI_DISPLAY_PROVIDER") == "xvfb"
                    ):
                        self._place_window_on_xvfb()
                    elif not self._private:
                        self._move_assetto_corsa_window()
                    return
                time.sleep(0.05)
            raise TimeoutError("Assetto Corsa did not become ready for direct capture")
        finally:
            client.stop()

    def _launch_assetto_corsa(self):
        env = None
        if self._direct:
            images = self._config["capture"]["images"]
            env = os.environ.copy()
            env["ACI_FRAME_SOCKET"] = images["socket_path"]
            env["ACI_FRAME_PROCESS"] = "acs.exe"
            env["VK_ADD_LAYER_PATH"] = os.pathsep.join(
                filter(
                    None, (images["vulkan_layer_path"], env.get("VK_ADD_LAYER_PATH"))
                )
            )
            env["VK_INSTANCE_LAYERS"] = os.pathsep.join(
                filter(None, ("VK_LAYER_ACI_game_frame", env.get("VK_INSTANCE_LAYERS")))
            )
            env["DXVK_LOG_PATH"] = images["diagnostic_path"]
            env["DXVK_LOG_LEVEL"] = "info"
        self._p_game = subprocess.Popen(
            ["/opt/cxoffice/bin/wine", "--bottle", self._bottle, "--cx-app", "acs.exe"],
            cwd=self._game_dir,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=None if self._direct else subprocess.DEVNULL,
        )

    def _shutdown_assetto_corsa(self):
        if self._direct:
            if self._p_game is not None and self._p_game.poll() is None:
                self._p_game.terminate()
                try:
                    self._p_game.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._p_game.kill()
                    self._p_game.wait(timeout=2)
        else:
            subprocess.run(["pkill", "acs.exe"])

    def _launch_sate_server(self):
        """
        Launch state server
        """
        self._try_until_state_server_is_launched()

    def _try_until_state_server_is_launched(self):
        if self._test_connection_to_server():
            if self._direct:
                raise RuntimeError(
                    "Refusing to reuse an existing telemetry server on port 6002"
                )
            return

        self._maybe_start_state_server()
        deadline = time.monotonic() + STATE_SERVER_STARTUP_TIMEOUT
        try:
            while time.monotonic() < deadline:
                status = self._p_state_server.poll()
                if status is not None:
                    self._state_server_log_reader.join(timeout=1)
                    output = "".join(self._state_server_log.copy()).strip()
                    raise RuntimeError(
                        f"CrossOver state server exited with status {status}: {output}"
                    )
                if self._test_connection_to_server():
                    return
                time.sleep(0.25)
            raise TimeoutError(
                f"CrossOver state server did not respond within "
                f"{STATE_SERVER_STARTUP_TIMEOUT} seconds"
            )
        except BaseException:
            self._shutdown_state_server()
            raise

    def _maybe_start_state_server(self):
        self._state_server_log.clear()
        self._p_state_server = subprocess.Popen(
            [
                "/opt/cxoffice/bin/wine",
                "--bottle",
                self._bottle,
                "--cx-app",
                "C:/Program Files/Python311/python.exe",
                "-m",
                "acs.server",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        # Wine needs a pipe for Python's standard output in this bottle.
        self._state_server_log_reader = Thread(
            target=self._read_state_server_log,
            args=(self._p_state_server.stdout,),
            daemon=True,
        )
        self._state_server_log_reader.start()

    def _read_state_server_log(self, stream):
        with stream:
            for line in stream:
                self._state_server_log.append(line)

    def _shutdown_state_server(self):
        """
        Shutdown state server
        """
        if self._p_state_server is not None:
            if self._p_state_server.poll() is None:
                self._p_state_server.terminate()
                try:
                    self._p_state_server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._p_state_server.kill()
                    self._p_state_server.wait()
            self._p_state_server = None
        if self._state_server_log_reader is not None:
            self._state_server_log_reader.join(timeout=1)
            self._state_server_log_reader = None

    def _setup_steam_appid_path(self):
        """
        Add path to steam app id file for Assetto Corsa
        """
        self._steam_appid_file_path = self._game_dir / "steam_appid.txt"


class DockerCrossOverLauncher(AssettoCorsaLauncher):
    def _launch_assetto_corsa(self):
        """
        Launches AC
        """
        with open("/execution_pipes/aci_execution_pipe", "w") as f:
            f.write("crossover_launch_ac\n")

    def _shutdown_assetto_corsa(self):
        """
        Shutdown AC
        """
        with open("/execution_pipes/aci_execution_pipe", "w") as f:
            f.write("crossover_shutdown_ac\n")

    def _launch_sate_server(self):
        """
        Launch state server
        """
        with open("/execution_pipes/aci_execution_pipe", "w") as f:
            f.write("crossover_launch_server\n")

    def _shutdown_state_server(self):
        """
        Shutdown state server
        """
        with open("/execution_pipes/aci_execution_pipe", "w") as f:
            f.write("crossover_shutdown_server\n")
