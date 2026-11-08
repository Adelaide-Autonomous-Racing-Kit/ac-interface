import multiprocessing as mp
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

from aci.game_capture.inference import GameCapture
from aci.game_capture.video.game_frame import FrameCaptureError
from acs.shared_memory.ac.combined import COMBINED_DATA_TYPES
import numpy as np
from test_game_frame import Producer


class Telemetry:
    def __init__(self):
        self.update_thread = self
        self._latest_state = {"state": bytes(np.dtype(COMBINED_DATA_TYPES).itemsize)}

    def is_alive(self):
        return True

    def stop(self):
        pass


@unittest.skipUnless(mp.get_start_method() == "fork", "ACI uses Linux fork")
class CaptureObservationsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.endpoint = Path(directory.name) / "test.sock"

    def start_capture(self, wait):
        capture = GameCapture(
            {
                "capture": {
                    "images": {
                        "backend": "game_frame",
                        "socket_path": str(self.endpoint),
                        "wait_for_new_frames": wait,
                        "startup_timeout_s": 1,
                    }
                },
                "video.ini": {"VIDEO": {"WIDTH": 2, "HEIGHT": 2}},
            }
        )
        with patch("aci.game_capture.inference.StateClient", Telemetry):
            capture.start()
        self.addCleanup(capture.stop)
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                producer = Producer(self.endpoint)
            except (ConnectionRefusedError, FileNotFoundError):
                time.sleep(0.01)
            else:
                self.addCleanup(producer.close)
                return capture, producer
        self.fail("Capture listener did not start")

    def test_telemetry_update_reuses_frame_but_reports_stale(self):
        capture, producer = self.start_capture(wait=False)
        producer.publish(1)
        first = capture.capture
        second = capture.capture
        self.assertFalse(first["is_image_stale"])
        self.assertTrue(second["is_image_stale"])
        self.assertIs(first["image"], second["image"])
        self.assertEqual(first["image_metadata"], second["image_metadata"])

    def test_wait_for_new_frame_unblocks_on_worker_kill(self):
        capture, producer = self.start_capture(wait=True)
        producer.publish(1)
        self.assertFalse(capture.capture["is_image_stale"])
        self.assertTrue(capture.is_stale)
        os.kill(capture.pid, signal.SIGKILL)
        with self.assertRaisesRegex(FrameCaptureError, "Game capture stopped"):
            capture.capture

    def test_lost_game_connection_reaches_observation_consumer(self):
        capture, producer = self.start_capture(wait=True)
        producer.publish(1)
        capture.capture
        producer.socket.shutdown(1)
        with self.assertRaisesRegex(FrameCaptureError, "producer disconnected"):
            capture.capture


if __name__ == "__main__":
    unittest.main()
