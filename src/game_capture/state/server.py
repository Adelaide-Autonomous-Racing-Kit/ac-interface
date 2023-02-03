from multiprocessing.connection import Listener
from threading import Thread
import ctypes
from src.game_capture.state.scraper import AssettoCorsaData

ADDRESS = "localhost"
PORT = 6002


class StateServer:
    """
    Socket server that sends game state updates to StateClients
        The underlying `AssettoCorsaData` class continualy scrapes
        the game state from memory and if an update step has occured
        the new state is sent to all clients connected

    """

    def __init__(self):
        self.assetto_corsa_data = AssettoCorsaData()
        self.listener = Listener((ADDRESS, PORT))
        self.is_running = True

    @property
    def game_state(self) -> ctypes.Structure:
        return self.assetto_corsa_data.shared_memory

    @property
    def latest_packet_id(self) -> int:
        return self.assetto_corsa_data.shared_memory["packetId"]

    def send_game_state(self, connection):
        last_packet_id = -1
        is_connected = True
        while is_connected:
            if not last_packet_id == self.latest_packet_id:
                try:
                    connection.send(self.assetto_corsa_data.shared_memory)
                    last_packet_id = self.assetto_corsa_data.shared_memory["packetId"]
                except Exception as e:
                    print(f"Connection Closed: {e}")
                    connection.close()
                    is_connected = False

    def run(self):
        while self.is_running:
            connection = self.listener.accept()
            worker = Thread(target=self.send_game_state, args=[connection], daemon=True)
            worker.start()


if __name__ == "__main__":
    state_server = StateServer()
    state_server.run()
