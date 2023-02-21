from multiprocessing.connection import Client
from threading import Thread
import time

from loguru import logger
import numpy as np
from src.game_capture.state.server import ADDRESS, PORT


class StateClient:
    """
    Socket client that receives game state updates from a StateServer
        It continually refreshes the current game state which can be
        access via the `latest_state` property
    """

    def __init__(self):
        self.client = Client((ADDRESS, PORT))
        self.__start_update_thread()
        self._latest_state = None
        self._is_stale = True
        self.is_running = True

    @property
    def new_state(self) -> np.array:
        """
        Waits until an unread state is ready to be read
        """
        self._wait_for_fresh_reading()
        return self._latest_state

    def _wait_for_fresh_reading(self):
        """
        Blocking call that waits until a new state from the game is received
        """
        while self._is_stale:
            continue
        self._is_stale = True

    @property
    def latest_state(self) -> np.array:
        """
        Returns the current state held by the object even if it has been read before
        """
        self._wait_for_first_reading()
        return self._latest_state

    def _wait_for_first_reading(self):
        """
        Blocking call that waits until the first state from the game is received
        """
        while self._latest_state is None:
            continue

    @property
    def is_AC_ready(self) -> bool:
        """
        :return: True if the packet ID recieved is above 500
        :rtype: bool
        """
        return self.latest_state["physics_packet_id"] > 500

    def wait_until_AC_is_ready(self):
        """
        Blocks execution until the game is ready for the session to be started
        """
        self._wait_for_packet_id_reset()
        while not self.is_AC_ready:
            continue

    def _wait_for_packet_id_reset(self):
        """
        Block until a packet ID close to zero is observed indicating the a new
            game session has started.
        """
        while not self.latest_state["physics_packet_id"] < 500:
            continue

    def __start_update_thread(self):
        """
        Starts a thread that consumes states yield by the state server
        """
        self.is_running = True
        self.update_thread = Thread(target=self._run, daemon=True)
        self.update_thread.start()

    def _run(self):
        while self.is_running:
            game_state = self.client.recv()
            self._latest_state = game_state
            self._is_stale = False


# Example test loops and benchmarking
def main():
    state_client = StateClient()
    print_state_output(state_client)
    benchmark_polling_rate(state_client)


def print_state_output(state_client):
    for _ in range(10):
        logger.info("=== Reading from AC ===")
        state = state_client.latest_state
        logger.info(f"Graphics Packet ID: {state['graphics_packet_id']}")
        logger.info(f"Physics Packet ID: {state['physics_packet_id']}")
        time.sleep(0.25)


def benchmark_polling_rate(state_client):
    logger.info(
        "Benchmarking rate at which state updates are received from the simulator"
    )
    n_reads = 900
    start_time = time.time()
    for _ in range(n_reads):
        _ = state_client.new_state
    elapsed_time = time.time() - start_time
    logger.info(
        f"Received {n_reads} states in {elapsed_time}s {n_reads/elapsed_time}Hz"
    )


if __name__ == "__main__":
    main()
