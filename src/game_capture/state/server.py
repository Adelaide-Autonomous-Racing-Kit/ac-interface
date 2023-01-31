from multiprocessing.connection import Listener
from threading import Thread
import ctypes
from src.game_capture.state.shared_memory import AssettoCorsaData

ADDRESS = "localhost"
PORT = 6001


class StateServer:
    def __init__(self):
        self.assetto_corsa_data = AssettoCorsaData()
        self.listener = Listener((ADDRESS, PORT))
        self.is_running = True

    @property
    def game_state(self) -> ctypes.Structure:
        return self.assetto_corsa_data.shared_memory

    @property
    def latest_packet_id(self) -> int:
        return self.assetto_corsa_data.shared_memory.packetId

    def send_game_state(self, connection):
        last_packet_id = -1
        while True:
            if not last_packet_id == self.latest_packet_id:
                connection.send(self.assetto_corsa_data.shared_memory)

    def run(self):
        while self.is_running:
            connection = self.listener.accept()
            worker = Thread(target=self.send_game_state, args=[connection], daemon=True)
            worker.start()


if __name__ == "__main__":
    state_server = StateServer()
    state_server.run()
