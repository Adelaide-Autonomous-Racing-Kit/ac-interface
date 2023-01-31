from multiprocessing.connection import Client
from threading import Thread

from src.game_capture.state.server import ADDRESS, PORT
from src.game_capture.state.shared_memory import SHMStruct


class StateClient:
    """
    Socket client that recievs game state updates from a StateServer
        It continuasly refreshes the current game state which can be
        access via the `latest_state` property
    """

    def __init__(self):
        self.client = Client((ADDRESS, PORT))
        self.__start_update_thread()
        self._latest_state = None
        self.is_running = True

    @property
    def latest_state(self) -> SHMStruct:
        self.wait_for_first_reading()
        return self._latest_state

    def wait_for_first_reading(self):
        """
        Blocking call that waits until first state from the game is recieved
        """
        while self._latest_state is None:
            pass

    def __start_update_thread(self):
        """
        Starts a thread that consumes state yieled by the state server
        """
        self.is_running = True
        self.update_thread = Thread(target=self._run, daemon=True)
        self.update_thread.start()

    def _run(self):
        while self.is_running:
            game_state = self.client.recv()
            self._latest_state = game_state


def main():
    state_client = StateClient()
    for _ in range(30):
        print(state_client.latest_state.throttle)


if __name__ == "__main__":
    main()
