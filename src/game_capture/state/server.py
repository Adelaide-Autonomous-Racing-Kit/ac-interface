import ctypes
from multiprocessing.connection import Listener
import socket
from threading import Thread

from loguru import logger
from src.game_capture.state.scraper import AssettoCorsaData

ADDRESS = "localhost"
PORT = 6001


class StateServer:
    """
    Socket server that sends game state updates to StateClients
        The underlying `AssettoCorsaData` class continually scrapes
        the game state from memory and if an update step has occurred
        the new state is sent to all clients connected

    """

    def __init__(self):
        self.assetto_corsa_data = AssettoCorsaData()
        self.listener = Listener((ADDRESS, PORT))
        self.__set_socket_options()
        self.is_running = True
        logger.info(f"State server created, listing on {ADDRESS}:{PORT}")

    def send_game_state(self, connection):
        last_packet_id = -1
        is_connected = True
        while is_connected:
            game_state = self.assetto_corsa_data.game_state
            if not last_packet_id == game_state["graphics_packet_id"]:
                try:
                    connection.send(game_state)
                    last_packet_id = game_state["graphics_packet_id"]
                except Exception as e:
                    print(f"Connection Closed: {e}")
                    connection.close()
                    is_connected = False

    def run(self):
        while self.is_running:
            connection = self.listener.accept()
            worker = Thread(target=self.send_game_state, args=[connection], daemon=True)
            worker.start()

    def __set_socket_options(self):
        self.listener._listener._socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )


if __name__ == "__main__":
    try:
        state_server = StateServer()
        state_server.run()
    except Exception as e:
        logger.info(e)
