import multiprocessing as mp
import shutil

from loguru import logger
from typing import Dict

from src.tools.data_generation.workers.base import (
    BaseWorker,
    WorkerSharedState,
)
from src.tools.data_generation.workers.generator import (
    depth,
    normals,
    segmentation,
)

DATA_GENERATORS = {
    "depth": depth.DepthMapGenerator,
    "normals": normals.NormalMapGenerator,
    "segmentation": segmentation.SegmentationGenerator,
}


class DataGenerationWorker(BaseWorker):
    def __init__(self, configuration: Dict, shared_state: WorkerSharedState):
        """
        Generates ground truth training data from recordings captured
            using the asseto corsa interface. Currently generates
            semantic segmentation maps, normal maps and depth maps.
            The depth and normal maps are scaled for visualisation.
        """
        super().__init__(configuration, shared_state)
        self._data_generators = []

    def _is_work_complete(self) -> bool:
        return self.is_ray_casting_done and self._job_queue.empty()

    def _do_work(self):
        self._save_ground_truth_data()
        self.increment_n_complete()

    def _save_ground_truth_data(self):
        [data_generator.generate() for data_generator in self._data_generators]
        self._copy_frame()

    def _copy_frame(self):
        filename = self._record_number + ".jpeg"
        source_path = self.recording_path.joinpath(filename)
        destination_path = self.output_path.joinpath(filename)
        shutil.copyfile(source_path, destination_path)

    @property
    def _job_queue(self) -> mp.Queue:
        return self.generation_queue

    @property
    def _record_number(self) -> str:
        return self._work["record_number"]

    def _setup(self):
        logger.info("Setting up data generation worker...")
        self._setup_scene()
        self._setup_data_generators()
        logger.info("Setup complete")
        self.set_as_ready()

    def _setup_data_generators(self):
        for data_type in self._config["generate"]:
            self._add_data_generator(data_type)

    def _add_data_generator(self, data_type: str):
        data_generator = DATA_GENERATORS[data_type](self)
        self._data_generators.append(data_generator)
