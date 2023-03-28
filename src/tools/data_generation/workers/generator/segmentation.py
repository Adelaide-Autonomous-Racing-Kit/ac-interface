import numpy as np
import trimesh

from src.tools.data_generation.workers.generator.base import DataGenerator
from src.tools.data_generation.workers.generator.utils import (
    allocate_empty_frame,
    rgb_to_bgr,
)

from src.tools.data_generation.tracks.constants import (
    COLOUR_LIST,
    TRAIN_ID_LIST,
)
from src.tools.data_generation.tracks import TRACK_DATA


class SegmentationGenerator(DataGenerator):
    def generate(self):
        pixel_ids = self._get_semantic_pixel_ids()
        for method in self._generation_methods:
            method(pixel_ids)

    def _get_semantic_pixel_ids(self) -> np.array:
        i_tri = np.copy(self._i_triangles)
        i_tri[i_tri != -1] = self._triangle_to_id[i_tri[i_tri != -1]]
        if self._is_generating_depth:
            pixel_ids = -1 * (allocate_empty_frame(*self._image_size) + 1)
            self._insert_values_into_image(i_tri, pixel_ids)
        else:
            pixel_ids = i_tri.reshape(self._image_size)
        return pixel_ids

    def _generate_visualised_semantics(self, pixel_ids: np.array):
        visualised_map = get_visualised_semantics(pixel_ids)
        self._save_colour_map(visualised_map)

    def _save_colour_map(self, colour_map: np.array):
        self._save_data(f"{self._record_number}-colour.png", colour_map)

    def _generate_semantic_training_data(self, pixel_ids: np.array):
        id_map = get_semantic_training_data(pixel_ids)
        self._save_segmentation_map(id_map)

    def _save_segmentation_map(self, ids_map: np.array):
        self._save_data(f"{self._record_number}-trainids.png", ids_map)

    def _setup(self):
        self._setup_triangle_to_id_map()
        self._register_generation_methods()

    def _setup_triangle_to_id_map(self):
        scene, track_name = self._worker._scene, self._worker.track_name
        triangle_to_id = get_triangle_to_semantic_id_map(scene, track_name)
        self._triangle_to_id = triangle_to_id

    def _register_generation_methods(self):
        generator_config = self._worker._config["generate"]["segmentation"]
        if "visuals" in generator_config:
            method = self._generate_visualised_semantics
            self._generation_methods.append(method)
        if "data" in generator_config:
            method = self._generate_semantic_training_data
            self._generation_methods.append(method)


def get_triangle_to_semantic_id_map(
    scene: trimesh.Scene,
    track_name: str,
) -> np.array:
    """
    Returns a mapping between triangle indexes and the semantic ID of
        that triangle's geometry.
    """
    triangle_to_node = scene.triangles_node
    material_to_id = TRACK_DATA[track_name].material_to_id
    triangle_to_id = [material_to_id[name] for name in triangle_to_node]
    return np.asarray(triangle_to_id, dtype=np.uint8)


def get_semantic_training_data(pixel_ids: np.array) -> np.array:
    id_map = np.array(TRAIN_ID_LIST[pixel_ids], dtype=np.uint8)
    return id_map


def get_visualised_semantics(pixel_ids: np.array) -> np.array:
    visualised_map = np.array(COLOUR_LIST[pixel_ids], dtype=np.uint8)
    visualised_map = rgb_to_bgr(visualised_map)
    return visualised_map
