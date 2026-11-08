"""Receive complete, unscaled SDR frames from the game-only Vulkan present layer."""

import fcntl
import math
import mmap
import os
from pathlib import Path
import select
import socket
import struct
import time

import numpy as np

# magic, version, width, height, format, pitch, sequence, present-hook timestamp.
HEADER = struct.Struct("<6I2Q")
MAGIC = int.from_bytes(b"ACIF", "little")
BGRA, RGBA = 1, 2
PIXELS = 4


class FrameCaptureError(RuntimeError):
    """The direct frame source stopped or sent an incompatible frame."""


class GameFrameStream:
    def __init__(self, config):
        self.width, self.height = map(int, config["resolution"])
        self.format = config["image_format"]
        self.path = Path(config["socket_path"])
        self.slot = self.path.with_suffix(".frame")
        self.startup_timeout = float(config.get("startup_timeout_s", 15))
        self.frame_timeout = float(config.get("frame_timeout_s", 5))
        if not all(
            math.isfinite(t) and t > 0
            for t in (self.startup_timeout, self.frame_timeout)
        ):
            raise ValueError("Direct frame timeouts must be positive and finite")
        if not (
            0 < self.width <= 4096
            and 0 < self.height <= 4096
            and self.format in {"RGB", "BGR", "BGR0"}
        ):
            raise ValueError("Unsupported direct frame dimensions or output format")
        if not self.path.is_absolute() or self.path.suffix != ".sock":
            raise ValueError("Direct capture needs an absolute .sock path")
        parent = self.path.parent.stat()
        if parent.st_uid != os.getuid() or parent.st_mode & 0o077:
            raise ValueError("Direct frame socket needs a private launch directory")

        self._size = HEADER.size + self.width * self.height * PIXELS
        self._fd = self._memory = self._listener = self._connection = None
        self._owns_slot = self._owns_socket = self._pending = self._ended = False
        self._sequence = self._dropped = 0
        self._deadline = time.monotonic() + self.startup_timeout
        try:
            self._fd = os.open(self.slot, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            self._owns_slot = True
            os.ftruncate(self._fd, self._size)
            os.write(
                self._fd,
                HEADER.pack(
                    MAGIC, 1, self.width, self.height, 0, self.width * PIXELS, 0, 0
                ),
            )
            self._memory = mmap.mmap(self._fd, self._size, access=mmap.ACCESS_READ)
            self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            self._listener.bind(str(self.path))
            self._owns_socket = True
            self._listener.listen(1)
            self._listener.setblocking(False)
        except BaseException:
            self.close()
            raise

    def read_latest(self, timeout=0):
        """Return (image, metadata), or None if no presentation is available yet."""
        if self._ended and not self._pending:
            raise FrameCaptureError("Vulkan frame producer disconnected")
        endpoint = self._connection or self._listener
        remaining = max(0, self._deadline - time.monotonic())
        ready, _, _ = select.select([endpoint], [], [], min(timeout, remaining))
        if ready and self._connection is None:
            self._connection, _ = self._listener.accept()
            self._connection.setblocking(False)
        if ready and self._connection is not None:
            self._drain_notifications()
        if self._pending:
            frame = self._read_slot()
            if frame is not None:
                self._deadline = time.monotonic() + self.frame_timeout
                return frame
        if time.monotonic() >= self._deadline:
            if self._sequence:
                raise FrameCaptureError("Vulkan frame stream stopped presenting")
            raise FrameCaptureError(
                "No direct Vulkan frames arrived; check the game renderer and layer log"
            )
        return None

    def _drain_notifications(self):
        # Notifications only wake the reader. Read the newest complete shared slot once.
        for _ in range(64):
            try:
                message, _, flags, _ = self._connection.recvmsg(512)
            except BlockingIOError:
                break
            if not message:
                self._ended = True
                if not self._pending:
                    raise FrameCaptureError("Vulkan frame producer disconnected")
                break
            if flags & socket.MSG_TRUNC:
                raise FrameCaptureError("Oversized direct frame notification")
            if message.startswith(b"E"):
                raise FrameCaptureError(message[1:].decode(errors="replace"))
            if message != b"F":
                raise FrameCaptureError("Invalid direct frame notification")
            self._pending = True

    def _read_slot(self):
        try:
            fcntl.flock(self._fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return None
        try:
            magic, version, w, h, fmt, pitch, seq, source_ns = HEADER.unpack_from(
                self._memory
            )
            if (
                (magic, version) != (MAGIC, 1)
                or (w, h, pitch) != (self.width, self.height, self.width * PIXELS)
                or fmt not in (BGRA, RGBA)
                or not source_ns
                or not seq
                or seq < self._sequence
            ):
                raise FrameCaptureError("Incompatible or malformed direct frame header")
            self._pending = False
            if seq == self._sequence:
                return None
            image = np.ndarray(
                (h, w, PIXELS), dtype=np.uint8, buffer=self._memory, offset=HEADER.size
            ).copy()
            received_ns = time.monotonic_ns()
        finally:
            fcntl.flock(self._fd, fcntl.LOCK_UN)

        if (fmt == BGRA and self.format == "RGB") or (
            fmt == RGBA and self.format != "RGB"
        ):
            image[:, :, [0, 2]] = image[:, :, [2, 0]]
        if self.format == "BGR0":
            image[:, :, 3] = 0
        else:
            image = np.ascontiguousarray(image[:, :, :3])
        self._dropped += seq - self._sequence - 1
        self._sequence = seq
        return image, {
            "frame_id": seq,
            "present_hook_ns": source_ns,
            "received_ns": received_ns,
            "source_drops": self._dropped,
        }

    def close(self):
        for resource in (self._connection, self._listener, self._memory):
            if resource is not None:
                resource.close()
        if self._fd is not None:
            os.close(self._fd)
        if self._owns_socket:
            self.path.unlink(missing_ok=True)
        if self._owns_slot:
            self.slot.unlink(missing_ok=True)
        self._connection = self._listener = self._memory = self._fd = None
        self._owns_socket = self._owns_slot = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
