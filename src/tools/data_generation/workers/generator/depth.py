import numpy as np
import trimesh

from loguru import logger

from src.tools.data_generation.workers.generator.base import DataGenerator
from src.tools.data_generation.workers.generator.utils import (
    allocate_empty_frame,
    noramlise_values,
    reverse_sign_of_values,
    convert_to_uint8,
)


class DepthMapGenerator(DataGenerator):
    def generate(self):
        [method() for method in self._generation_methods]

    def _generate_visualised_depth_map(self):
        depth_map = self._get_depth_map()
        self._save_depth_map(depth_map)

    def _get_depth_map(self):
        depth = self._calculate_depth()
        self._visualise_depth_map(depth)
        depth_map = allocate_empty_frame(*self._image_size)
        self._insert_values_into_image(depth, depth_map)
        return depth_map

    def _calculate_depth(self) -> np.array:
        return calculate_depth(self._hit_to_camera, self._ray_directions)

    def _visualise_depth_map(self, depth: np.array):
        noramlise_values(depth)
        reverse_sign_of_values(depth)
        convert_to_uint8(depth)

    def _save_depth_map(self, depth_map: np.array):
        self._save_data(f"{self._record_number}-depth.png", depth_map)

    def _setup(self):
        self._register_generation_methods()

    def _register_generation_methods(self):
        generator_config = self._worker._config["generate"]["depth"]
        if "visuals" in generator_config:
            method = self._generate_visualised_depth_map
            self._generation_methods.append(method)
        if "data" in generator_config:
            raise NotImplementedError()


def calculate_depth(hit_to_camera: np.array, directions: np.array) -> np.array:
    return trimesh.util.diagonal_dot(hit_to_camera, directions)
