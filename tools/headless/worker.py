"""Enter the private X server before loading any desktop-aware modules."""

import csv
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def private_display():
    display = os.environ.get("DISPLAY", "")
    provider = os.environ.get("ACI_DISPLAY_PROVIDER")
    if (
        not re.fullmatch(r":[0-9]+(?:\.0)?", display)
        or display.split(".")[0] == os.environ.get("ACI_DESKTOP_DISPLAY")
        or provider not in {"gamescope", "xvfb"}
        or (provider == "gamescope" and not os.environ.get("GAMESCOPE_WAYLAND_DISPLAY"))
        or (provider == "xvfb" and not os.environ.get("XAUTHORITY"))
    ):
        raise RuntimeError(
            f"No distinct private X display from {provider}: {display!r}"
        )
    from Xlib.display import Display

    connection = Display(display)
    try:
        if not connection.has_extension("XTEST"):
            raise RuntimeError(
                f"Private {provider} display lacks XTEST; use a Gamescope build with libei "
                "or select --display-provider xvfb"
            )
        from Xlib import X
        from Xlib.ext import xtest

        root = connection.screen().root
        pointer = root.query_pointer()
        target = (8, 8) if (pointer.root_x, pointer.root_y) != (8, 8) else (16, 16)
        xtest.fake_input(connection, X.MotionNotify, x=target[0], y=target[1])
        connection.sync()
        moved = root.query_pointer()
        if (moved.root_x, moved.root_y) != target:
            raise RuntimeError(f"Private {provider} display did not accept XTEST input")
        xtest.fake_input(connection, X.MotionNotify, x=pointer.root_x, y=pointer.root_y)
        connection.sync()
    finally:
        connection.close()
    os.environ["ACI_PRIVATE_DISPLAY"] = display


def show_dashboard_on_desktop(output):
    from acmpc.dashboard import dashboard

    desktop = os.environ["ACI_DASHBOARD_DISPLAY"]
    authority = os.environ.get("ACI_DASHBOARD_XAUTHORITY")
    runtime = os.environ.get("ACI_DASHBOARD_RUNTIME")
    agent_pid = os.getpid()

    class DesktopDashboard(dashboard.DashBoardProcess):
        def _setup_providers(self, engine):
            super()._setup_providers(engine)
            self._app.aboutToQuit.connect(self._stop_agent)

        def _stop_agent(self):
            if os.getppid() == agent_pid:
                (output / "dashboard-closed").touch()
                os.kill(agent_pid, signal.SIGINT)

        def run(self):
            # Only this forked Qt child connects to the desktop. PyAutoGUI,
            # CrossOver, and the capture worker keep the private DISPLAY.
            os.environ["DISPLAY"] = desktop
            os.environ["QT_QPA_PLATFORM"] = "xcb"
            for name, value in (
                ("XAUTHORITY", authority),
                ("XDG_RUNTIME_DIR", runtime),
            ):
                if value:
                    os.environ[name] = value
                else:
                    os.environ.pop(name, None)
            print(f"Agent Dashboard starting on desktop display {desktop}", flush=True)
            super().run()

    # The agent imports the dashboard class during the collection worker's setup.
    dashboard.DashBoardProcess = DesktopDashboard


def main(runtime, config, output, bottle, steam):
    desktop_proof = os.environ.get("ACI_DISPLAY_PROVIDER") == "desktop"
    if not desktop_proof:
        private_display()
        print(
            f"Assetto Corsa will use private display {os.environ['DISPLAY']}",
            flush=True,
        )
    if os.environ.get("ACI_DASHBOARD_DISPLAY"):
        show_dashboard_on_desktop(output)
    sys.path.insert(0, str(runtime))
    import frame_recording
    import live_lap

    class DirectFrameRecorder(frame_recording.FrameRecorder):
        def __init__(self, directory, camera):
            super().__init__(directory, camera)
            self._timing = (self.directory / "direct-frames.csv").open("w", newline="")
            self._timing_writer = csv.DictWriter(
                self._timing,
                fieldnames=[
                    "host_observation_ns",
                    "frame_id",
                    "present_hook_ns",
                    "received_ns",
                    "source_drops",
                    "capture_drops",
                ],
            )
            self._timing_writer.writeheader()

        def submit(self, observation, timestamp_ns=None):
            timestamp_ns = time.monotonic_ns() if timestamp_ns is None else timestamp_ns
            accepted = super().submit(observation, timestamp_ns)
            if accepted:
                self._timing_writer.writerow(
                    {
                        "host_observation_ns": timestamp_ns,
                        **observation["image_metadata"],
                    }
                )
                self._timing.flush()
            return accepted

        def close(self):
            try:
                super().close()
                manifest = self.directory / "manifest.json"
                data = json.loads(manifest.read_text())
                data["direct_frame_metadata"] = {
                    "file": "direct-frames.csv",
                    "join_on": "host_observation_ns in frames.csv",
                    "clock": "CLOCK_MONOTONIC nanoseconds on the host",
                    "present_hook_ns": "Entry to the native present hook, before GPU readback",
                    "received_ns": "Complete frame copied into the Python receiver",
                    "source_drops": "Cumulative lock drops and overwritten unread receiver frames",
                    "capture_drops": "Cumulative received frames missed before the observation read",
                }
                manifest.write_text(json.dumps(data, indent=2) + "\n")
            finally:
                self._timing.close()

    # Keep the existing worker, driving settings, and JPEG preprocessing.
    frame_recording.FrameRecorder = DirectFrameRecorder
    live_lap.CONFIG = config
    if desktop_proof or os.environ.get("ACI_REUSE_DESKTOP_STEAM") == "1":
        return live_lap.worker(output)
    with (output / "steam.log").open("w") as log:
        steam_process = subprocess.Popen(
            [
                "/opt/cxoffice/bin/wine",
                "--bottle",
                bottle,
                "--cx-app",
                "C:/Program Files (x86)/Steam/steam.exe",
                "-silent",
            ],
            cwd=steam.parent,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            # Give Steam a head start in the private bottle. The AC launcher
            # has its own readiness deadline and reports any launch failure.
            time.sleep(8)
            return live_lap.worker(output)
        finally:
            if steam_process.poll() is None:
                steam_process.terminate()


if __name__ == "__main__":
    if sys.argv[1:] == ["--check-display"]:
        private_display()
        print(f"Private display {os.environ['DISPLAY']} accepted XTEST input.")
        sys.exit(0)
    runtime, config, output, bottle, steam = sys.argv[1:]
    sys.exit(main(Path(runtime), Path(config), Path(output), bottle, Path(steam)))
