"""Run the Monza collection worker with direct Vulkan capture."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

from aci.config.constants import CONFIG_FILES, STEAM_APPID, crossover_paths
import yaml

HERE = Path(__file__).resolve().parent
WINE = Path("/opt/cxoffice/bin/wine")
SIZE = (1280, 736)
PORT = 6002


def read_environment(pid):
    try:
        return set((Path("/proc") / str(pid) / "environ").read_bytes().split(b"\0"))
    except OSError:
        return set()


def assert_free(prefix, *, reuse_steam=False):
    with socket.socket() as endpoint:
        endpoint.settimeout(0.5)
        if endpoint.connect_ex(("127.0.0.1", PORT)) == 0:
            raise RuntimeError(f"Telemetry port {PORT} is already in use")
    for task in Path("/proc").glob("[0-9]*"):
        try:
            if task.stat().st_uid != os.getuid():
                continue
            name = (task / "comm").read_text().strip().lower()
        except OSError:
            continue
        if name == "acs.exe" or (
            not reuse_steam
            and b"WINEPREFIX=" + os.fsencode(prefix) in read_environment(task.name)
        ):
            raise RuntimeError(
                f"An AC or isolated bottle process is still running (PID {task.name})"
            )


def bottle_paths(bottle, *, reuse_steam=False):
    if not reuse_steam and bottle == "Assetto_Corsa":
        raise RuntimeError("Headless collection requires a separate CrossOver bottle")
    capture = {"crossover_bottle": bottle}
    steam, user = crossover_paths({"capture": capture})
    prefix = (Path.home() / ".cxoffice" / bottle).absolute()
    if not prefix.is_dir() or prefix.resolve() != prefix:
        raise RuntimeError(f"Prepare an independent CrossOver bottle at {prefix}")
    steam_client = prefix / "drive_c/Program Files (x86)/Steam/steam.exe"
    setup = user / "setups/ks_audi_r8_lms_2016/monza/0.ini"
    appid = steam / "steam_appid.txt"
    files = {name: user / "cfg" / name for name in CONFIG_FILES}
    files["monza-0.ini"] = setup
    # CrossOver commonly links Documents to the host. Reject symlinks out of the
    # isolated bottle and hard links before opening anything for writing.
    for path in (steam, steam_client, steam / "acs.exe", appid, *files.values()):
        if not reuse_steam and not path.resolve().is_relative_to(prefix):
            raise RuntimeError(
                f"Isolated bottle path points outside the bottle: {path}"
            )
        if path.is_file() and path.stat().st_nlink != 1:
            raise RuntimeError(f"Isolated bottle contains a shared file: {path}")
    if not all(path.is_file() for path in (steam_client, steam / "acs.exe", appid)):
        raise RuntimeError("The CrossOver bottle needs Steam, AC, and steam_appid.txt")
    if appid.read_text().strip() != STEAM_APPID:
        raise RuntimeError(f"Set {appid} to {STEAM_APPID} in the isolated bottle")
    if not (user / "cfg").is_dir():
        raise RuntimeError(
            f"Missing AC configuration in isolated bottle: {user / 'cfg'}"
        )
    return prefix, steam_client, files


def find_display_program(args):
    if args.desktop_proof:
        return None
    if args.display_provider == "gamescope":
        display_program = shutil.which(args.gamescope)
        if not display_program or not shutil.which("Xwayland"):
            raise RuntimeError(
                "Gamescope and Xwayland are required (or select --display-provider xvfb)"
            )
        help_result = subprocess.run(
            [display_program, "--help"], capture_output=True, text=True, timeout=10
        )
        help_text = help_result.stdout + help_result.stderr
        if "--backend" not in help_text or "headless" not in help_text:
            raise RuntimeError(
                "This Gamescope build does not advertise the headless backend"
            )
    else:
        display_program = shutil.which("xvfb-run")
        if not display_program or not shutil.which("Xvfb") or not shutil.which("xauth"):
            raise RuntimeError(
                "The Xvfb provider needs xvfb-run, Xvfb and xauth on PATH"
            )
    return display_program


def display_command(provider, program):
    if provider == "desktop":
        return []
    width, height = map(str, SIZE)
    if provider == "gamescope":
        return [
            program,
            "--backend",
            "headless",
            "-w",
            width,
            "-h",
            height,
            "-W",
            width,
            "-H",
            height,
            "-r",
            "60",
            "--",
        ]
    return [
        program,
        "--auto-servernum",
        "--server-args",
        f"-screen 0 {width}x{height}x24 -nolisten tcp",
        "--",
    ]


def display_env(session, provider, *, dashboard=False, reuse_steam=False):
    env = os.environ.copy()
    env["ACI_DESKTOP_DISPLAY"] = env.get("DISPLAY", "").split(".")[0]
    for key in (
        "ACI_DASHBOARD_DISPLAY",
        "ACI_DASHBOARD_XAUTHORITY",
        "ACI_DASHBOARD_RUNTIME",
    ):
        env.pop(key, None)
    if dashboard:
        env["ACI_DASHBOARD_DISPLAY"] = env["DISPLAY"]
        env["ACI_DASHBOARD_XAUTHORITY"] = env.get("XAUTHORITY", "")
        env["ACI_DASHBOARD_RUNTIME"] = env.get("XDG_RUNTIME_DIR", "")
    if reuse_steam:
        env["ACI_REUSE_DESKTOP_STEAM"] = "1"
    else:
        env.pop("ACI_REUSE_DESKTOP_STEAM", None)
    if provider == "desktop":
        env.update(ACI_SESSION_TOKEN=session.name, ACI_DISPLAY_PROVIDER=provider)
        return env
    for key in (
        "DISPLAY",
        "XAUTHORITY",
        "WAYLAND_DISPLAY",
        "WAYLAND_SOCKET",
        "STEAM_GAME_DISPLAY_0",
        "GAMESCOPE_WAYLAND_DISPLAY",
        "WINEPREFIX",
        "CX_BOTTLE",
        "CX_BOTTLE_PATH",
        "WINELOADER",
        "WINESERVER",
        "ACI_PRIVATE_DISPLAY",
    ):
        env.pop(key, None)
    env.update(
        XDG_RUNTIME_DIR=str(session),
        ACI_SESSION_TOKEN=session.name,
        ACI_DISPLAY_PROVIDER=provider,
    )
    return env


def preflight(args):
    display_program = find_display_program(args)
    layer = args.layer.resolve()
    for name in ("aci_frame.json", "libaci_game_frame.so"):
        if not (layer / name).is_file():
            raise RuntimeError(f"Missing {layer / name}; run make in {HERE}")
    if not WINE.is_file():
        raise RuntimeError("CrossOver is required")
    if not os.access("/dev/uinput", os.W_OK):
        raise RuntimeError(
            "The existing virtual controller requires access to /dev/uinput"
        )
    reuse_steam = args.desktop_proof or args.reuse_desktop_steam
    prefix, steam_client, files = bottle_paths(args.bottle, reuse_steam=reuse_steam)
    assert_free(prefix, reuse_steam=reuse_steam)
    if args.dashboard or reuse_steam:
        from Xlib.display import Display

        desktop = Display(os.environ["DISPLAY"])
        desktop.close()
    if reuse_steam:
        display = os.environ["DISPLAY"].split(".")[0]
        expected = b"WINEPREFIX=" + os.fsencode(prefix)
        for task in Path("/proc").glob("[0-9]*"):
            try:
                name = (task / "comm").read_text().strip().lower()
            except OSError:
                continue
            if name != "steam.exe":
                continue
            env = read_environment(task.name)
            if expected in env and any(
                item.startswith(b"DISPLAY=")
                and item.decode().split("=")[1].split(".")[0] == display
                for item in env
            ):
                break
        else:
            raise RuntimeError(
                "Start Steam in the default CrossOver bottle on the desktop first"
            )
    for path in (
        "live_lap.py",
        "frame_recording.py",
        "config/monza-crossover.yaml",
        "assets/0.ini",
        "assets/audi_r8_lms_2016/car.ini",
        "assets/monza-fpn-resnet-18-v1.1.pt",
        "assets/monza_verysmooth.npy",
    ):
        if not (args.runtime / path).is_file():
            raise RuntimeError(f"Missing prepared runtime file: {args.runtime / path}")
    return display_program, layer, prefix, steam_client, files


@contextmanager
def run_lock():
    # Coordinate multiple headless supervisors for the single ac-state port.
    location = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    fd = os.open(
        location / "aci-headless-6002.lock",
        os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR,
        0o600,
    )
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another headless supervisor owns port 6002") from error
        yield
    finally:
        os.close(fd)


def owned_wine_processes(prefix, token):
    wanted = {
        b"WINEPREFIX=" + os.fsencode(prefix),
        b"ACI_SESSION_TOKEN=" + token.encode(),
    }
    for task in Path("/proc").glob("[0-9]*"):
        if wanted <= read_environment(task.name):
            yield int(task.name)


def stop_owned(process, prefix, token):
    if process is None:
        return
    for sig, timeout in ((signal.SIGINT, 5), (signal.SIGTERM, 3), (signal.SIGKILL, 2)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        # Wine can detach from the Gamescope process group. Match both launch
        # token and bottle, and pin the PID before signalling it.
        for pid in owned_wine_processes(prefix, token):
            try:
                fd = os.pidfd_open(pid)
            except ProcessLookupError:
                continue
            try:
                if pid in owned_wine_processes(prefix, token):
                    signal.pidfd_send_signal(fd, sig)
            except ProcessLookupError:
                pass
            finally:
                os.close(fd)
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            process.poll()
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                if not any(owned_wine_processes(prefix, token)):
                    return
            time.sleep(0.1)
    raise RuntimeError("Could not stop all owned processes; settings backup retained")


def stage_config(runtime, layer, socket_path, bottle, output, *, private_display=True):
    config = yaml.safe_load((runtime / "config/monza-crossover.yaml").read_text())
    aci = config["aci"]
    video = aci["video.ini"]["VIDEO"]
    if (int(video["WIDTH"]), int(video["HEIGHT"])) != SIZE:
        raise RuntimeError(
            "The headless comparison requires the baseline 1280x736 config"
        )
    capture = aci["capture"]
    if capture["is_docker"] or capture["is_proton"]:
        raise RuntimeError(
            "The headless runner requires the local CrossOver configuration"
        )
    capture.update(private_display=private_display, crossover_bottle=bottle)
    # Preserve the existing control loop cadence. Telemetry-only samples still
    # report the previous image as stale; only new images enter the recorder.
    capture["images"].update(
        backend="game_frame",
        socket_path=str(socket_path),
        vulkan_layer_path=str(layer),
        diagnostic_path=str(output),
    )
    target = output / "run-config.yaml"
    target.write_text(yaml.safe_dump(config, sort_keys=False))
    return target


def supervise(args):
    with run_lock():
        display_program, layer, prefix, steam_client, files = preflight(args)
        if args.check:
            print(
                f"Direct capture preflight passed: {args.display_provider}, {prefix}. No game was launched."
            )
            return 0
        output = args.output.resolve() / datetime.now(timezone.utc).strftime(
            ("desktop-proof" if args.desktop_proof else "headless")
            + "-%Y%m%dT%H%M%S.%fZ"
        )
        output.mkdir(parents=True, mode=0o700)
        backup = output / "backup"
        backup.mkdir()
        for name, path in files.items():
            if path.is_file():
                shutil.copy2(path, backup / name)
        print(f"Logs: {output}", flush=True)
        return supervise_owned(
            args, display_program, layer, prefix, steam_client, files, output, backup
        )


def supervise_owned(
    args, display_program, layer, prefix, steam_client, files, output, backup
):
    result = {
        "completed": False,
        "capture_backend": "game_frame",
        "logs": str(output),
        "display_provider": args.display_provider,
        "capture_protocol_version": 1,
    }
    process = None
    settings_staged = False
    with tempfile.TemporaryDirectory(prefix="aci-") as directory:
        session = Path(directory)
        token = session.name
        try:
            config = stage_config(
                args.runtime,
                layer,
                session / "capture.sock",
                args.bottle,
                output,
                private_display=not args.desktop_proof,
            )
            files["monza-0.ini"].parent.mkdir(parents=True, exist_ok=True)
            settings_staged = True
            shutil.copy2(args.runtime / "assets/0.ini", files["monza-0.ini"])
            env = display_env(
                session,
                args.display_provider,
                dashboard=args.dashboard,
                reuse_steam=args.reuse_desktop_steam,
            )
            command = display_command(args.display_provider, display_program)
            if args.display_provider == "gamescope":
                version = subprocess.run(
                    [display_program, "--version"],
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=10,
                )
                result["display_version"] = (version.stdout or version.stderr).strip()
            command += [
                sys.executable,
                str(HERE / "worker.py"),
                str(args.runtime),
                str(config),
                str(output),
                args.bottle,
                str(steam_client),
            ]
            with (output / "agent.log").open("w") as log:
                process = subprocess.Popen(
                    command,
                    env=env,
                    cwd=args.runtime.parent / "ac-mpc",
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                deadline = time.monotonic() + 120
                driving = False
                while process.poll() is None:
                    if not driving and (output / "driving-started").exists():
                        driving = True
                        deadline = time.monotonic() + (
                            20 if args.desktop_proof else 600
                        )
                        snapshot = output / "effective-game-config"
                        snapshot.mkdir()
                        for name, path in files.items():
                            if path.is_file():
                                shutil.copy2(path, snapshot / name)
                    if (output / "lap-result.json").is_file():
                        try:
                            process.wait(timeout=15)
                        except subprocess.TimeoutExpired:
                            result["cleanup_warning"] = (
                                "Worker did not finish after reporting the lap"
                            )
                        break
                    if time.monotonic() >= deadline:
                        if driving and args.desktop_proof:
                            result["stop_reason"] = (
                                "finished the 20-second desktop capture test"
                            )
                            process.send_signal(signal.SIGINT)
                            try:
                                process.wait(timeout=15)
                            except subprocess.TimeoutExpired:
                                result["cleanup_warning"] = (
                                    "Agent did not stop promptly"
                                )
                        else:
                            result["stop_reason"] = (
                                "lap timeout" if driving else "startup timeout"
                            )
                        break
                    time.sleep(0.25)
                lap = output / "lap-result.json"
                if lap.is_file():
                    result.update(json.loads(lap.read_text()))
                    if (
                        process.poll() != 0
                        or not (output / "recording/manifest.json").is_file()
                    ):
                        result.update(
                            completed=False,
                            stop_reason="Lap reported but recording did not finish cleanly",
                        )
                elif (output / "dashboard-closed").is_file():
                    result["stop_reason"] = "Agent Dashboard closed"
                else:
                    result.setdefault(
                        "stop_reason",
                        f"Collection exited before completing a timed lap (status {process.poll()})",
                    )
        except KeyboardInterrupt:
            result["stop_reason"] = "interrupted"
        except Exception as error:
            result["stop_reason"] = str(error)
        finally:
            try:
                stop_owned(process, prefix, token)
                if settings_staged:
                    for name, path in files.items():
                        if (backup / name).is_file():
                            shutil.copy2(backup / name, path)
                            if path.read_bytes() != (backup / name).read_bytes():
                                raise RuntimeError(
                                    f"Could not verify restoration of {path}"
                                )
                        else:
                            path.unlink(missing_ok=True)
                result["settings_restored"] = True
            except (OSError, RuntimeError) as error:
                result.update(settings_restored=False, cleanup_error=str(error))
            manifest = output / "recording/manifest.json"
            if manifest.is_file():
                result["recorded_frames"] = json.loads(manifest.read_text()).get(
                    "frames", 0
                )
            (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    success = (
        result.get("recorded_frames", 0) > 0
        if args.desktop_proof
        else result["completed"]
    )
    return 0 if success and result["settings_restored"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--bottle", default="Assetto_Corsa_Headless")
    parser.add_argument("--gamescope", default="gamescope")
    parser.add_argument(
        "--display-provider", choices=("gamescope", "xvfb"), default="gamescope"
    )
    parser.add_argument("--layer", type=Path, default=HERE / "build")
    parser.add_argument("--output", type=Path, default=HERE / "logs")
    parser.add_argument(
        "--check", action="store_true", help="Check prerequisites without starting AC"
    )
    parser.add_argument(
        "--check-display",
        action="store_true",
        help="Test private display and startup input without starting Wine or AC",
    )
    parser.add_argument(
        "--desktop-proof",
        action="store_true",
        help="Use the existing desktop Steam session and capture 20 seconds of the default agent",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Show the Python Agent Dashboard on the desktop while the game uses the private display",
    )
    parser.add_argument(
        "--reuse-desktop-steam",
        action="store_true",
        help="Use Steam already running in the default bottle; launch AC on the private Xvfb display",
    )
    args = parser.parse_args()
    if args.reuse_desktop_steam:
        if args.display_provider != "xvfb" or args.desktop_proof:
            parser.error("--reuse-desktop-steam requires the private Xvfb provider")
        args.bottle = "Assetto_Corsa"
    if args.desktop_proof:
        if args.check_display:
            parser.error("--check-display is for private displays")
        args.bottle = "Assetto_Corsa"
        args.display_provider = "desktop"
    args.runtime = args.runtime.resolve()
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        if args.check_display:
            program = find_display_program(args)
            with tempfile.TemporaryDirectory(prefix="aci-display-") as directory:
                session = Path(directory)
                env = display_env(session, args.display_provider)
                command = display_command(args.display_provider, program)
                process = subprocess.Popen(
                    command
                    + [sys.executable, str(HERE / "worker.py"), "--check-display"],
                    env=env,
                    start_new_session=True,
                )
                try:
                    return process.wait(timeout=20)
                finally:
                    stop_owned(process, session, session.name)
        return supervise(args)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Headless AC: {error}\n")


def interrupted(*_):
    raise KeyboardInterrupt


if __name__ == "__main__":
    sys.exit(main())
