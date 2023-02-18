import ctypes
import mmap
import struct
import time
from threading import Lock, Thread
from typing import Dict, List, Tuple

import numpy as np
from loguru import logger

from src.game_capture.state.shared_memory.ac.physics import PhysicsSharedMemory
from src.game_capture.state.shared_memory.ac.graphics import GraphicsSharedMemory
from src.game_capture.state.shared_memory.ac.combined import COMBINED_DATA_TYPES


class AssettoCorsaData:
    """
    Continuously copies the shared memory buffer state from Assetto Corsa
    """

    def __init__(self):
        self._physics_memory_map = mmap.mmap(
            -1,
            ctypes.sizeof(PhysicsSharedMemory),
            "Local\\acpmf_physics",
            access=mmap.ACCESS_READ,
        )
        self._graphics_memory_map = mmap.mmap(
            -1,
            ctypes.sizeof(GraphicsSharedMemory),
            "Local\\acpmf_graphics",
            access=mmap.ACCESS_READ,
        )
        self.update_lock = Lock()
        self.update_thread = Thread(target=self._run, daemon=True)
        self.update_thread.start()

    def _run(self):
        while True:
            self._update()

    def _update(self):
        self._reset_buffer_positions()
        self._read_from_buffers()

    def _reset_buffer_positions(self):
        self._physics_memory_map.seek(0)
        self._graphics_memory_map.seek(0)

    def _read_from_buffers(self):
        graphics_bytes = read_memory(self._graphics_memory_map, GraphicsSharedMemory)
        physics_bytes = read_memory(self._physics_memory_map, PhysicsSharedMemory)
        with self.update_lock:
            self.graphics_packet_id = struct.unpack("i", graphics_bytes[0])[0]
            self.physics_packet_id = struct.unpack("i", physics_bytes[0])[0]
            self.combined_byte_string = graphics_bytes[1] + physics_bytes[1]
            # self.shared_memory = buffer_to_numpy(combined_buffer, COMBINED_DATA_TYPES)

    @property
    def game_state(self) -> Dict:
        with self.update_lock:
            game_state = {"physics_packet_id": self.physics_packet_id}
            game_state["graphics_packet_id"] = self.graphics_packet_id
            game_state["state"] = self.combined_byte_string
        return game_state


def read_memory(mmap: mmap.mmap, shared_memory_struct: ctypes.Structure) -> bytes:
    packet_id = mmap.read(ctypes.sizeof(ctypes.c_int))
    return packet_id, mmap.read(ctypes.sizeof(shared_memory_struct))


def buffer_to_numpy(raw_bytes: bytes, combined_data_types: List[Tuple]) -> np.array:
    return np.frombuffer(raw_bytes, combined_data_types)


# Small test loop for debugging
def main():
    acd = AssettoCorsaData()
    time.sleep(1)
    while True:
        logger.info(f"Physics Packet ID: {acd.physics_packet_id}")
        logger.info(f"Graphics Packet ID: {acd.graphics_packet_id}")
        time.sleep(10)


if __name__ == "__main__":
    main()
