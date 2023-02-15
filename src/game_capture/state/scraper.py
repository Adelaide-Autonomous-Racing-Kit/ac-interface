import ctypes
import mmap
import time
from threading import Thread
import numpy as np

from src.game_capture.state.shared_memory.physics import PhysicsSharedMemory
from src.game_capture.state.shared_memory.graphics import GraphicsSharedMemory


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
        # self._physics = read_memory(self._physics_memory_map, PhysicsSharedMemory)
        self._graphics = read_memory(self._graphics_memory_map, GraphicsSharedMemory)


def read_memory(mmap: mmap.mmap, shared_memory_struct: ctypes.Structure) -> np.array:
    raw_data = mmap.read(ctypes.sizeof(shared_memory_struct))
    return np.frombuffer(raw_data, shared_memory_struct._fields_)


# Small test loop for debugging
def main():
    acd = AssettoCorsaData()
    time.sleep(1)
    while True:
        print("=== Simulation is running ===")
        for field in acd._graphics.dtype.names:
            print(f"{field}: {acd._graphics[field]}")
        time.sleep(10)


if __name__ == "__main__":
    main()
