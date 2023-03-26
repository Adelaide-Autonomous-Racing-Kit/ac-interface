import numpy as np
from typing import Dict

from src.tools.data_generation.worker import BaseWorker, SharedVariables
from src.tools.data_generation.utils import (
    allocate_empty_frame,
    get_semantic_training_data,
    get_triangle_to_semantic_id_mapping,
    get_triangle_to_normal_mapping,
    get_visualied_semantics,
)


class DataGenerationWorker(BaseWorker):
    def __init__(self, configuration: Dict, shared_state: SharedVariables):
        """
        Generates ground truth training data from recordings captured
            using the asseto corsa interface. Currently generates
            semantic segmentation maps, normal maps and depth maps.
            The depth and normal maps are scaled for visualisation.
        """
        super().__init__(configuration, shared_state)

    @property
    def _triangle_nodes(self) -> np.array:
        """
        Mapping fron triangle index to scene graph node ID
        """
        return self._scene.triangle_nodes

    def save_gorund_truth_data(self, record_number: str):
        # TODO: Replace with registered functions
        if self._is_generating_segmentation:
            self._generate_semantic_segmentation_data(record_number)
        if self._is_generating_depth:
            self._generate_depth_map(record_number)
        if self._is_generating_normals:
            self._generate_normal_map(record_number)
        self._copy_frame(record_number)

    def _generate_semantic_segmentation_data(self, record_number: str):
        pixel_ids = self._get_semantic_pixel_ids()
        # TODO: Replace with registered functions
        if self._is_generating_visualised_semantics:
            self._generate_visualised_semantics(record_number, pixel_ids)
        if self._is_generating_semantic_training_data:
            self._generate_semantic_training_data(record_number, pixel_ids)

    def _get_semantic_pixel_ids(self) -> np.array:
        i_tri = np.copy(self._i_triangles)
        i_tri[i_tri != -1] = self._triangle_ids[i_tri[i_tri != -1]]
        if self._is_generating_depth:
            pixel_ids = allocate_empty_frame(*self.image_size)
            self._insert_values_into_image(i_tri, pixel_ids)
        else:
            pixel_ids = i_tri.reshape(self.image_size)
        return pixel_ids

    def _generate_visualised_semantics(
        self,
        record_number: str,
        pixel_ids: np.array,
    ):
        visualised_map = get_visualied_semantics(pixel_ids)
        self._save_colour_map(record_number, visualised_map)

    def _save_colour_map(self, record_number: str, colour_map: np.array):
        self._save_data(f"{record_number}-colour.png", colour_map)

    def _generate_semantic_training_data(
        self,
        record_number: str,
        pixel_ids: np.array,
    ):
        id_map = get_semantic_training_data(pixel_ids)
        self._save_segmentation_map(record_number, id_map)

    def _save_segmentation_map(self, record_number: str, ids_map: np.array):
        self._save_data(f"{record_number}-trainids.png", ids_map)

    def _generate_normal_map(self, record_number: str):
        normal_map = self._get_normal_map()
        self._save_normal_map(record_number, normal_map)

    def _get_normal_map(self):
        normals = self._triangle_normals[self._i_triangles]
        noramlise_values(normals)
        convert_to_uint8(normals)
        if self._is_generating_depth:
            normal_map = self._allocate_empty_frame(channels=3)
            self._insert_values_into_image(normals, normal_map)
        else:
            normal_map = normals.reshape((*self.image_size, 3))
        return normal_map

    def _save_normal_map(self, record_number: str, normal_map: np.array):
        self._save_data(f"{record_number}-normals.png", normal_map)

    def _generate_depth_map(self, record_number: str):
        depth_map = self._get_depth_map()
        self._save_depth_map(record_number, depth_map)

    def _get_depth_map(self):
        depth = self._calculate_depth()
        noramlise_values(depth)
        reverse_sign_of_values(depth)
        convert_to_uint8(depth)
        depth_map = allocate_empty_frame()
        self._insert_values_into_image(depth, depth_map)
        return depth_map

    def _calculate_depth(self) -> np.array:
        hit_to_camera = self._locations - self._ray_origins[0]
        direction = self._ray_directions[self._i_rays]
        return trimesh.util.diagonal_dot(hit_to_camera, direction)

    def _save_depth_map(self, record_number: str, depth_map: np.array):
        self._save_data(f"{record_number}-depth.png", depth_map)

    def _save_data(self, filename: str, to_save: np.array):
        to_save = np.rot90(to_save)
        if not self._is_generating_depth:
            to_save = np.flipud(to_save)
        filepath = str(self.output_path.joinpath(filename))
        cv2.imwrite(filepath, to_save)

    def _insert_values_into_image(self, values: np.array, image: np.array):
        image[self._pixels_to_rays[:, 0], self._pixels_to_rays[:, 1]] = values

    def _copy_frame(self, record: str):
        source_path = self.recording_path.joinpath(record + ".jpeg")
        destination_path = self.output_path.joinpath(record + ".jpeg")
        shutil.copyfile(source_path, destination_path)
