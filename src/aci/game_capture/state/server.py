from multiprocessing.connection import Listener
import socket
import struct
from threading import Thread
from typing import Dict, Tuple

from loguru import logger
from aci.game_capture.state.scraper import AssettoCorsaData

ADDRESS = "localhost"
PORT = 6002


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
        self._unpack_int = struct.Struct("i").unpack
        logger.info(f"State server created, listing on {ADDRESS}:{PORT}")

    def send_state(self, connection):
        last_packet_id = (-1, -1)
        is_connected = True
        while is_connected:
            game_state = self.assetto_corsa_data.game_state
            current_packet_id = self._get_packet_id(game_state)
            if not last_packet_id == current_packet_id:
                is_connected = self._send_state(connection, game_state)
                last_packet_id = current_packet_id

    def _get_packet_id(self, game_state: Dict) -> Tuple[int]:
        state_bytes = game_state["state"]
        n_completed_laps = self._unpack_int(state_bytes[128:132])[0]
        i_current_time = self._unpack_int(state_bytes[136:140])[0]
        return (n_completed_laps, i_current_time)

    def _send_state(self, connection: socket, game_state: Dict):
        try:
            connection.send(game_state)
            return True
        except Exception as e:
            logger.info((f"Connection Closed: {e}"))
            connection.close()
            return False

    def run(self):
        while self.is_running:
            connection = self.listener.accept()
            worker = Thread(target=self.send_state, args=[connection], daemon=True)
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
