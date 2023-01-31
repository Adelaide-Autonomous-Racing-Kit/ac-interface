import ctypes
import mmap
import time
from threading import Thread

from src.game_capture.state.shared_memory import SHMStruct


class AssettoCorsaData:
    """
    Continuously copies the shared memory buffer state from Assetto Corsa
    """

    def __init__(self):
        self._physics_memory_map = mmap.mmap(
            -1,
            ctypes.sizeof(SHMStruct),
            "Local\\acpmf_physics",
            access=mmap.ACCESS_READ,
        )
        self.update_thread = Thread(target=self._run, daemon=True)
        self.update_thread.start()
        self.initial_packetId = self.shared_memory.packetId
        self._has_AC_started = False

    def _run(self):
        while True:
            self._update()

    def _update(self):
        self._physics_memory_map.seek(0)
        raw_data = self._physics_memory_map.read(ctypes.sizeof(SHMStruct))
        shared_memory = SHMStruct.from_buffer_copy(raw_data)
        self.shared_memory = shared_memory

    def has_AC_started(self):
        if self.shared_memory.packetId != self.initial_packetId:
            self._has_AC_started = True
        return self._has_AC_started


# Small test loop for debugging
def main():
    acd = AssettoCorsaData()
    while True:
        if acd.has_AC_started():
            print("=== Simulation is running ===")
            for field in acd.shared_memory._fields_:
                value = eval(f"acd.shared_memory.{field[0]}")
                print(f"{field[0]}: {value}")
            time.sleep(10)


if __name__ == "__main__":
    main()
