"""Measure direct-frame delivery against a controlled headless Vulkan test pattern."""

import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile
import time

from aci.game_capture.video.game_frame import FrameCaptureError, GameFrameStream
import numpy as np


def benchmark(build, duration, fps, xcb=False):
    ages = []
    frames = 0
    changes = 0
    previous = None
    previous_id = 0
    first_ns = last_ns = None
    cpu_start = time.process_time()
    with tempfile.TemporaryDirectory(prefix="aci-bench-") as run:
        endpoint = str(Path(run) / "capture.sock")
        config = dict(
            resolution=(1280, 736),
            image_format="BGR0",
            socket_path=endpoint,
        )
        with GameFrameStream(config) as receiver:
            env = dict(
                os.environ,
                ACI_FRAME_SOCKET=endpoint,
                ACI_FRAME_PROCESS="smoke",
                VK_ADD_LAYER_PATH=os.pathsep.join(
                    filter(None, (str(build), os.environ.get("VK_ADD_LAYER_PATH")))
                ),
                VK_INSTANCE_LAYERS=os.pathsep.join(
                    filter(
                        None,
                        (
                            "VK_LAYER_ACI_game_frame",
                            os.environ.get("VK_INSTANCE_LAYERS"),
                        ),
                    )
                ),
            )
            if xcb:
                env["ACI_SMOKE_XCB"] = "1"
            else:
                env.pop("DISPLAY", None)
            env.pop("WAYLAND_DISPLAY", None)
            start = time.monotonic()
            producer = subprocess.Popen(
                [build / "smoke", str(duration), str(fps)], env=env
            )
            try:
                while time.monotonic() - start < duration + 20:
                    try:
                        frame = receiver.read_latest(0.1)
                    except FrameCaptureError as error:
                        if str(error) == "Vulkan frame producer disconnected":
                            break
                        raise
                    if frame is None:
                        if producer.poll() is not None:
                            raise RuntimeError(
                                f"Vulkan smoke process exited: {producer.returncode}"
                            )
                        continue
                    image, metadata = frame
                    assert metadata["frame_id"] > previous_id
                    previous_id = metadata["frame_id"]
                    last_ns = metadata["received_ns"]
                    if first_ns is None:
                        first_ns = last_ns
                    green = int(image[0, 0, 1])
                    assert green in (16, 240)
                    assert tuple(image[0, 0]) == (0, green, 255, 0)
                    assert tuple(image[-1, -1]) == (255, green, 0, 0)
                    assert tuple(image[-1, 0]) == (255, green, 255, 0)
                    assert tuple(image[0, -1]) == (0, green, 0, 0)
                    changes += previous != green
                    previous = green
                    frames += 1
                    ages.append(
                        (metadata["received_ns"] - metadata["present_hook_ns"]) / 1e6
                    )
                elapsed = time.monotonic() - start
                if producer.wait(timeout=5):
                    raise RuntimeError(
                        f"Vulkan smoke process exited: {producer.returncode}"
                    )
            finally:
                if producer.poll() is None:
                    producer.kill()
                    producer.wait()
    if not frames or changes < 2:
        raise RuntimeError("No moving Vulkan frames received")
    receive_span = (last_ns - first_ns) / 1e9
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "frames": frames,
        "changed_test_patterns": changes,
        "elapsed_s": elapsed,
        "received_fps": (frames - 1) / receive_span,
        "receiver_cpu_s": time.process_time() - cpu_start,
        "producer_cpu_s": child_usage.ru_utime + child_usage.ru_stime,
        "hook_to_receive_first_minute_p95_ms": float(
            np.percentile(ages[: 60 * fps], 95)
        ),
        "hook_to_receive_last_minute_p95_ms": float(
            np.percentile(ages[-60 * fps :], 95)
        ),
        "source_drops": previous_id - frames,
        "hook_to_receive_ms": dict(
            zip(
                ("p50", "p95", "p99", "max"),
                np.percentile(ages, [50, 95, 99, 100]).tolist(),
            )
        ),
    }
    print(json.dumps(result, indent=2))
    if result["received_fps"] < min(30, fps * 0.95):
        raise RuntimeError("Direct delivery missed the frame-rate floor")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=5)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--build", type=Path, default=Path(__file__).parent / "build")
    parser.add_argument(
        "--xcb", action="store_true", help="Use the supplied private X display"
    )
    args = parser.parse_args()
    benchmark(args.build.resolve(), args.seconds, args.fps, args.xcb)
