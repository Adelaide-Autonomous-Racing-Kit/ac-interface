import numpy as np
import trimesh

from src.tools.data_generation.workers.generator.base import DataGenerator
from src.tools.data_generation.workers.generator.utils import (
    allocate_empty_frame,
    noramlise_values,
    convert_to_uint8,
)


class NormalMapGenerator(DataGenerator):
    def generate(self):
        [method() for method in self._generation_methods]

    def _generate_visualised_normal_map(self):
        normal_map = self._get_normal_map()
        self._save_normal_map(normal_map)

    def _get_normal_map(self):
        normals = self._triangle_to_normal[self._i_triangles]
        self._visualise_normal_map(normals)
        if self._is_generating_depth:
            shape = self._image_size
            normal_map = allocate_empty_frame(*shape, channels=3)
            self._insert_values_into_image(normals, normal_map)
        else:
            normal_map = normals.reshape((*self._image_size, 3))
        return normal_map

    def _visualise_normal_map(self, normals: np.array):
        noramlise_values(normals)
        convert_to_uint8(normals)

    def _save_normal_map(self, normal_map: np.array):
        self._save_data(f"{self._record_number}-normals.png", normal_map)

    def _setup(self):
        self._setup_triangle_to_normal_map()
        self._register_generation_methods()

    def _setup_triangle_to_normal_map(self):
        triangle_to_normal = get_triangle_to_normal_map(self._worker._scene)
        self._triangle_to_normal = triangle_to_normal

    def _register_generation_methods(self):
        generator_config = self._worker._config["generate"]["normals"]
        if "visuals" in generator_config:
            method = self._generate_visualised_normal_map
            self._generation_methods.append(method)
        if "data" in generator_config:
            raise NotImplementedError()


def get_triangle_to_normal_map(scene: trimesh.Scene) -> np.array:
    """
    Returns a mapping between triangle indexes and the normal vector of
        that triangle's face.
    """
    normals, valid = trimesh.triangles.normals(scene.triangles)
    triangle_to_normal = np.zeros((valid.shape[0], 3), dtype=np.float32)
    triangle_to_normal[valid] = normals
    return triangle_to_normal
