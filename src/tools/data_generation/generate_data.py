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
from src.tools.data_generation.worker import BaseWorker, SharedVariables
from src.tools.data_generation.ray_caster import RayCastingWorker
from src.tools.data_generation.data_generator import DataGenerationWorker


# TODO: Clean this shit hole
class MultiprocessDataGenerator:
    def __init__(self, configuration_path: str):
        self._config = load_yaml(configuration_path)
        self._n_ray_casting_workers = self._config["n_ray_casting_workers"]
        self._n_generation_workers = self._config["n_generation_workers"]
        self._log_configuration()
        self.__setup_folders()
        self.__initialise_member_variables()
        self.__setup_workers()

    @property
    def output_path(self) -> Path:
        return Path(self._config["output_path"])

    def __setup_folders(self):
        maybe_create_folders(self.output_path)

    def _log_configuration(self):
        pass

    def __initialise_member_variables(self):
        self._ray_casting_queue = mp.Queue()
        self._generation_queue = mp.Queue()
        self._n_completed = mp.Value("i", 0)
        self._is_ray_casting_done = mp.Value(ctypes.c_bool, False)
        self._ray_casting_workers, self._generation_workers = [], []
        self.is_generation_done, self.is_ray_casting_done = False, False
        self.is_ready = False

    def __setup_workers(self):
        logger.info(
            f"Creating {self._n_ray_casting_workers} ray casting worker(s)..."
        )
        for _ in range(self._n_ray_casting_workers):
            shared_state = self._create_shared_worker_state()
            worker = RayCastingWorker(self._config, shared_state)
            self._ray_casting_workers.append(worker)
        logger.info(
            f"Creating {self._n_generation_workers} generation worker(s)..."
        )
        for _ in range(self._n_generation_workers):
            shared_state = self._create_shared_worker_state()
            worker = DataGenerationWorker(self._config, shared_state)
            self._generation_workers.append(worker)

    def _create_shared_worker_state(self) -> SharedVariables:
        shared_state = SharedVariables(
            ray_cast_queue=self._ray_casting_queue,
            generation_queue=self._generation_queue,
            is_ray_casting_done=self._is_ray_casting_done,
            is_done=mp.Value(ctypes.c_bool, False),
            is_ready=mp.Value(ctypes.c_bool, False),
            n_complete=self._n_completed,
        )
        return shared_state

    @property
    def recording_path(self) -> Path:
        return Path(self._config["recorded_data_path"])

    @property
    def _workers(self) -> List[BaseWorker]:
        return [*self._ray_casting_workers, *self._generation_workers]

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
        # Populate ray casting queue
        records = self._get_subsample()
        [self._ray_casting_queue.put(record) for record in records]
        # Start worker processes
        [worker.start() for worker in self._workers]
        # Wait for works to run setup
        while not self.is_ready:
            self.is_ready = all([worker.is_ready for worker in self._workers])
            time.sleep(0.1)
        logger.info(f"Workers intialised sucessfully")

        # Monitor worker progress
        start_time, last_n_completed = time.time(), 0
        with tqdm(total=len(records)) as pbar:
            while not self._ray_casting_queue.empty():
                current_n_done = self._n_completed.value
                pbar.update(current_n_done - last_n_completed)
                last_n_completed = current_n_done
                time.sleep(0.2)
        # Wait for all ray casters to finish
        while not self.is_ray_casting_done:
            self.is_ray_casting_done = all(
                [worker.is_done for worker in self._ray_casting_workers]
            )
            time.sleep(0.1)
        self._is_ray_casting_done.value = True
        # Wait for generators to finish
        while not self.is_generation_done:
            self.is_generation_done = all(
                [worker.is_done for worker in self._generation_workers]
            )
            time.sleep(0.1)
        elapsed = time.time() - start_time
        # Finish off progress bar
        current_n_done = self._n_completed.value
        pbar.update(current_n_done - last_n_completed)
        logger.info(f"Generated {len(records)} samples in {elapsed}s")
        # Clean up workers
        [worker.terminate() for worker in self._workers]

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


if __name__ == "__main__":
    main()
