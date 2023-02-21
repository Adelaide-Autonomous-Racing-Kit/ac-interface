from typing import Dict

from loguru import logger
from src.game_capture.inference import GameCapture
from src.interface import AssettoCorsaInterface
from src.utils.launch import click_drive, try_until_state_server_is_launched
from src.utils.save import maybe_create_folders, save_bgr0_as_jpeg, save_bytes


class AssettoCorsaRecorder(AssettoCorsaInterface):
    """
    Class that records game sessions
    """

    def _initialise_capture(self):
        try_until_state_server_is_launched()
        self._game_capture = GameCapture(use_RGB_images=False, use_state_dicts=False)

    def behaviour(self, observation: Dict):
        pass

    def run(self, save_path: str):
        """
        Saves frames and state to disk as .jpeg, .npy file pairs
            Each sequential capture is stamped with a logical clock
            indicating their order
        """
        self.__setup_recording(save_path)
        self._launch_AC()
        self._start_capture()
        click_drive()
        logger.info("Starting to record game session")
        while self.is_running:
            try:
                self._write_capture_to_file()
            except KeyboardInterrupt:
                self.is_running = False
        logger.info("Finished recording")
        self.shutdown()

    def __setup_recording(self, save_path: str):
        self._save_path = save_path
        self.frame_count = 0
        maybe_create_folders(save_path)

    def _write_capture_to_file(self):
        observation = self.get_observation()
        save_bytes(f"{self._save_path}/{self.frame_count}", observation["state"])
        save_bgr0_as_jpeg(f"{self._save_path}/{self.frame_count}", observation["image"])
        self.frame_count += 1
