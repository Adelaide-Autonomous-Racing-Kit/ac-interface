import ctypes
import os
import time
import multiprocessing as mp
from pathlib import Path
from typing import List

from loguru import logger
from tqdm import tqdm

from src.utils.load import load_yaml
from src.utils.save import maybe_create_folders


"""
    def __setup_data_generators(self):
        self._is_generating_depth = "depth" in self._config["generate"]
        self._is_generating_normals = "normals" in self._config["generate"]
        self._is_generating_segmentation = (
            "segmentation" in self._config["generate"]
        )
        if self._is_generating_segmentation:
            self._is_generating_visualised_semantics = (
                "visuals" in self._config["generate"]["segmentation"]
            )
            self._is_generating_semantic_training_data = (
                "data" in self._config["generate"]["segmentation"]
            )
        else:
            self._is_generating_visualised_semantics = False
            self._is_generating_semantic_training_data = False
"""


# TODO: finetune camera position, dynamically import constants based on track
class MultiprocessDataGenerator:
    def __init__(self, configuration_path: str):
        self._config = load_yaml(configuration_path)
        self._n_workers = self._config["n_workers"]
        self._log_configuration()
        self.__setup_folders()
        self.__setup_workers(configuration_path)

    def __setup_folders(self):
        maybe_create_folders(self.output_path)

    def _log_configuration(self):
        pass

    def __setup_workers(self, configuration_path: str):
        self._shared_queue = mp.Queue()
        self._shared_n_done = mp.Value("i", 0)
        self._workers = []
        logger.info(f"Starting {self._n_workers} data generation workers...")
        for _ in range(self._n_workers):
            shared_is_done = mp.Value(ctypes.c_bool, False)
            shared_is_ready = mp.Value(ctypes.c_bool, False)
            worker = IntersectionWorker(
                configuration_path,
                self._shared_queue,
                shared_is_done,
                shared_is_ready,
                self._shared_n_done,
            )
            self._workers.append((worker, shared_is_done, shared_is_ready))

    @property
    def recording_path(self) -> Path:
        return Path(self._config["recorded_data_path"])

    def start(self):
        """
        Runs through each of the records specifed in the configuration file
            posting them to the pool of workers. For each record workers
            generate and save the following:
                - Visualised segmentation map
                - Segmentation map with train ids
                - Visualised normal map of the scene
                - Visualised depth map of the scene
            It also copies the original frame captured to the output folder
            to be used as input in the training dataset.
        """
        is_ready, is_done, last_n_done = False, False, 0
        records = self._get_subsample()
        [self._shared_queue.put(record) for record in records]
        [worker[0].start() for worker in self._workers]
        while not is_ready:
            is_ready = all([worker[2].value for worker in self._workers])
        logger.info(f"Workers intialised sucessfully")
        start_time = time.time()
        with tqdm(total=len(records)) as pbar:
            while not self._shared_queue.empty():
                current_n_done = self._shared_n_done.value
                pbar.update(current_n_done - last_n_done)
                time.sleep(0.5)
                last_n_done = current_n_done
        while not is_done:
            is_done = all([worker[1] for worker in self._workers])
            time.sleep(0.1)
        elapsed = time.time() - start_time
        current_n_done = self._shared_n_done.value
        pbar.update(current_n_done - last_n_done)
        logger.info(f"Generated {len(records)} samples in {elapsed}s")

    def _get_subsample(self):
        start = self._config["start_at_sample"]
        end = self._config["finish_at_sample"]
        interval = self._config["sample_every"]
        return self._get_sample_list()[start:end:interval]

    def _get_sample_list(self) -> List[str]:
        filenames = os.listdir(self.recording_path)
        samples = self._filter_for_game_state_files(filenames)
        return self._sort_records(samples)

    def _filter_for_game_state_files(self, filenames: List[str]) -> List[str]:
        return [record[:-4] for record in filenames if record[-4:] == ".bin"]

    def _sort_records(self, filenames: List[str]) -> List[str]:
        return sorted(filenames, key=lambda x: int(x))


def main():
    root_path = Path(os.path.dirname(__file__))
    config_path = root_path.joinpath("monza/config.yaml")
    data_generator = MultiprocessDataGenerator(config_path)
    data_generator.start()
    # data_generator = DataGenerator(config_path)
    # data_generator.generate_segmentation_data()


if __name__ == "__main__":
    main()
