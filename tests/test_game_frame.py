import fcntl
import mmap
import os
from pathlib import Path
import socket
import tempfile
import time
import unittest

from aci.game_capture.video.game_frame import (
    BGRA,
    HEADER,
    MAGIC,
    RGBA,
    FrameCaptureError,
    GameFrameStream,
)
import numpy as np


class Producer:
    def __init__(self, endpoint):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        try:
            self.socket.connect(str(endpoint))
            self.fd = os.open(endpoint.with_suffix(".frame"), os.O_RDWR)
        except BaseException:
            self.socket.close()
            raise
        self.memory = mmap.mmap(self.fd, 0)

    def publish(self, sequence, fmt=RGBA, version=1, size=(2, 2)):
        stamp = time.monotonic_ns()
        w, h = size
        with self:
            self.memory[: HEADER.size] = HEADER.pack(
                MAGIC, version, w, h, fmt, w * 4, sequence, stamp
            )
            self.memory[HEADER.size :] = bytes([250, 7, 2, 255] * 4)
        self.socket.send(b"F")
        return stamp

    def close(self):
        self.memory.close()
        os.close(self.fd)
        self.socket.close()

    def __enter__(self):
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.fd, fcntl.LOCK_UN)


class FrameStreamTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.endpoint = Path(directory.name) / "test.sock"

    def receiver(self, image_format="BGR0", **overrides):
        config = dict(
            resolution=(2, 2), image_format=image_format, socket_path=self.endpoint
        )
        config.update(overrides)
        receiver = GameFrameStream(config)
        self.addCleanup(receiver.close)
        return receiver

    def producer(self):
        producer = Producer(self.endpoint)
        self.addCleanup(producer.close)
        return producer

    def test_latest_complete_frame_and_drops(self):
        receiver = self.receiver()
        producer = self.producer()
        producer.publish(1)
        stamp = producer.publish(2)
        with producer:
            self.assertIsNone(receiver.read_latest())
        image, meta = receiver.read_latest()
        np.testing.assert_array_equal(image, np.tile([2, 7, 250, 0], (2, 2, 1)))
        self.assertEqual(meta["frame_id"], 2)
        self.assertEqual(meta["source_drops"], 1)
        self.assertEqual(meta["present_hook_ns"], stamp)
        self.assertGreaterEqual(meta["received_ns"], stamp)
        producer.socket.send(b"F")  # A wakeup can refer to a slot we already read.
        self.assertIsNone(receiver.read_latest())

    def test_rgb_and_padding(self):
        receiver = self.receiver("RGB")
        self.producer().publish(1, BGRA)
        image, _ = receiver.read_latest()
        np.testing.assert_array_equal(image, np.tile([2, 7, 250], (2, 2, 1)))
        self.assertTrue(image.flags.c_contiguous)

    def test_partial_header_or_resize_is_explicit(self):
        receiver = self.receiver()
        self.producer().publish(1, size=(1, 1))
        with self.assertRaisesRegex(FrameCaptureError, "malformed"):
            receiver.read_latest()

    def test_invalid_notification_is_explicit(self):
        receiver = self.receiver()
        self.producer().socket.send(b"FF")
        with self.assertRaisesRegex(FrameCaptureError, "Invalid"):
            receiver.read_latest()

    def test_disconnect_after_final_frame(self):
        receiver = self.receiver()
        producer = self.producer()
        producer.publish(1)
        producer.socket.shutdown(socket.SHUT_WR)
        self.assertEqual(receiver.read_latest()[1]["frame_id"], 1)
        with self.assertRaisesRegex(FrameCaptureError, "disconnected"):
            receiver.read_latest()
        receiver.close()
        self.assertFalse(self.endpoint.exists())
        self.assertFalse(self.endpoint.with_suffix(".frame").exists())

    def test_no_producer_times_out(self):
        receiver = self.receiver(startup_timeout_s=0.03)
        with self.assertRaisesRegex(FrameCaptureError, "No direct Vulkan frames"):
            receiver.read_latest(1)

    def test_telemetry_only_does_not_extend_frame_deadline(self):
        receiver = self.receiver(frame_timeout_s=0.03)
        self.producer().publish(1)
        self.assertIsNotNone(receiver.read_latest())
        with self.assertRaisesRegex(FrameCaptureError, "stopped presenting"):
            receiver.read_latest(1)


if __name__ == "__main__":
    unittest.main()
