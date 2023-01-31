from multiprocessing.connection import Client

from src.game_capture.state.server import ADDRESS, PORT


class StateClient:
    def __init__(self):
        self.client = Client((ADDRESS, PORT))
        self.is_running = True

    def run(self):
        while self.is_running:
            game_state = self.client.recv()


if __name__ == "__main__":
    state_client = StateClient()
    state_client.run()
