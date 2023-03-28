import abc
from pathlib import Path
from typing import Dict, List

import numpy as np

from src.tools.data_generation.workers.generator.utils import save_image


class DataGenerator:
    def __init__(self, worker_reference):
        self._worker = worker_reference
        self._generation_methods = []
        self._setup()

    @abc.abstractmethod
    def generate(self):
        """
        Implement data generation work specific to the data being created
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup(self):
        """
        Implement data generator specific setup steps
        """
        raise NotImplementedError()

    def _save_data(self, filename: str, to_save: np.array):
        flip_ud = not self._is_generating_depth
        output_path = self._output_path.joinpath(filename)
        save_image(to_save, output_path, flip_ud)

    def _insert_values_into_image(self, values: np.array, image: np.array):
        image[self._pixels_to_rays[:, 0], self._pixels_to_rays[:, 1]] = values

    @property
    def _generation_job(self) -> Dict:
        return self._worker._work

    @property
    def _output_path(self) -> Path:
        return Path(self._worker._config["output_path"])

    @property
    def _record_number(self) -> str:
        return self._worker._work["record_number"]

    @property
    def _i_triangles(self) -> np.array:
        return self._worker._work["i_triangles"]

    @property
    def _pixels_to_rays(self) -> np.array:
        return self._worker._work["pixels_to_rays"]

    @property
    def _hit_to_camera(self) -> np.array:
        locations = self._worker._work["locations"]
        origin = self._worker._work["origin"]
        return locations - origin

    @property
    def _ray_directions(self) -> np.array:
        directions = self._worker._work["ray_directions"]
        i_ray = self._worker._work["i_rays"]
        return directions[i_ray]

    @property
    def _is_generating_depth(self) -> bool:
        generation_config = self._worker._config["generate"]
        return "depth" in generation_config

    @property
    def _image_size(self) -> List[int]:
        return self._worker._config["image_size"]
