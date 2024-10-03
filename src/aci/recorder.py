from typing import Dict

from aci.game_capture.inference import GameCapture
from aci.interface import AssettoCorsaInterface
from aci.utils.save import maybe_create_folders, save_bgr0_as_jpeg, save_bytes
from loguru import logger


class AssettoCorsaRecorder(AssettoCorsaInterface):
    """
    Class that records game sessions
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self._save_path = config["recording"]["save_path"]

    def _initialise_capture(self):
        self._ac_launcher.launch_sate_server()
        self._game_capture = GameCapture(self._config)

    def behaviour(self, observation: Dict):
        pass

    def teardown(self):
        pass

    def termination_condition(self, observation: Dict) -> bool:
        return False

    def run(self):
        """
        Saves frames and state to disk as .jpeg, .npy file pairs
            Each sequential capture is stamped with a logical clock
            indicating their order
        """
        self.__setup_recording()
        self._launch_AC()
        self._start_capture()
        self._ac_launcher.click_drive()
        logger.info("Starting to record game session")
        while self.is_running:
            try:
                self._write_capture_to_file()
            except KeyboardInterrupt:
                self.is_running = False
        logger.info("Finished recording")
        self._shutdown()

    def __setup_recording(self):
        self.frame_count = 0
        maybe_create_folders(self._save_path)

    def _write_capture_to_file(self):
        observation = self.get_observation()
        save_bytes(f"{self._save_path}/{self.frame_count}", observation["state"])
        save_bgr0_as_jpeg(f"{self._save_path}/{self.frame_count}", observation["image"])
        self.frame_count += 1
