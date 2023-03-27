import multiprocessing as mp
import shutil

import numpy as np
from loguru import logger
from typing import Dict

from src.tools.data_generation.workers.utils import load_track_mesh
from src.tools.data_generation.workers.base import (
    BaseWorker,
    WorkerSharedState,
)
from src.tools.data_generation.workers.generator.utils import (
    allocate_empty_frame,
    calculate_depth,
    convert_to_uint8,
    get_semantic_training_data,
    get_triangle_to_semantic_id_mapping,
    get_triangle_to_normal_mapping,
    get_visualised_semantics,
    noramlise_values,
    save_image,
    reverse_sign_of_values,
)


# TODO: Split off each type of data into a class that are registered with the worker
#       Fix background colour map colour
class DataGenerationWorker(BaseWorker):
    def __init__(self, configuration: Dict, shared_state: WorkerSharedState):
        """
        Generates ground truth training data from recordings captured
            using the asseto corsa interface. Currently generates
            semantic segmentation maps, normal maps and depth maps.
            The depth and normal maps are scaled for visualisation.
        """
        super().__init__(configuration, shared_state)

    def _is_work_complete(self) -> bool:
        return self.is_ray_casting_done and self._job_queue.empty()

    def _do_work(self):
        self._save_ground_truth_data()
        self.increment_n_complete()

    def _save_ground_truth_data(self):
        # TODO: Replace with registered functions
        if self._is_generating_segmentation:
            self._generate_semantic_segmentation_data()
        if self._is_generating_depth:
            self._generate_depth_map()
        if self._is_generating_normals:
            self._generate_normal_map()
        self._copy_frame()

    def _generate_semantic_segmentation_data(self):
        pixel_ids = self._get_semantic_pixel_ids()
        # TODO: Replace with registered functions
        if self._is_generating_visualised_semantics:
            self._generate_visualised_semantics(pixel_ids)
        if self._is_generating_semantic_training_data:
            self._generate_semantic_training_data(pixel_ids)

    def _get_semantic_pixel_ids(self) -> np.array:
        i_tri = np.copy(self._i_triangles)
        i_tri[i_tri != -1] = self._triangle_to_id[i_tri[i_tri != -1]]
        if self._is_generating_depth:
            pixel_ids = allocate_empty_frame(*self.image_size)
            self._insert_values_into_image(i_tri, pixel_ids)
        else:
            pixel_ids = i_tri.reshape(self.image_size)
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

    def _generate_normal_map(self):
        normal_map = self._get_normal_map()
        self._save_normal_map(normal_map)

    def _get_normal_map(self):
        normals = self._triangle_to_normal[self._i_triangles]
        self._visualise_normal_map(normals)
        if self._is_generating_depth:
            shape = self.image_size
            normal_map = allocate_empty_frame(*shape, channels=3)
            self._insert_values_into_image(normals, normal_map)
        else:
            normal_map = normals.reshape((*self.image_size, 3))
        return normal_map

    def _visualise_normal_map(self, normals: np.array):
        noramlise_values(normals)
        convert_to_uint8(normals)

    def _save_normal_map(self, normal_map: np.array):
        self._save_data(f"{self._record_number}-normals.png", normal_map)

    def _generate_depth_map(self):
        depth_map = self._get_depth_map()
        self._save_depth_map(depth_map)

    def _get_depth_map(self):
        depth = self._calculate_depth()
        self._visualise_depth_map(depth)
        depth_map = allocate_empty_frame(*self.image_size)
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

    def _save_data(self, filename: str, to_save: np.array):
        flip_ud = not self._is_generating_depth
        output_path = self.output_path.joinpath(filename)
        save_image(to_save, output_path, flip_ud)

    def _insert_values_into_image(self, values: np.array, image: np.array):
        image[self._pixels_to_rays[:, 0], self._pixels_to_rays[:, 1]] = values

    def _copy_frame(self):
        filename = self._record_number + ".jpeg"
        source_path = self.recording_path.joinpath(filename)
        destination_path = self.output_path.joinpath(filename)
        shutil.copyfile(source_path, destination_path)

    @property
    def _generation_job(self) -> Dict:
        return self._work

    @property
    def _job_queue(self) -> mp.Queue:
        return self.generation_queue

    @property
    def _record_number(self) -> str:
        return self._generation_job["record_number"]

    @property
    def _i_triangles(self) -> np.array:
        return self._generation_job["i_triangles"]

    @property
    def _pixels_to_rays(self) -> np.array:
        return self._generation_job["pixels_to_rays"]

    @property
    def _hit_to_camera(self) -> np.array:
        locations = self._generation_job["locations"]
        origin = self._generation_job["origin"]
        return locations - origin

    @property
    def _ray_directions(self) -> np.array:
        directions = self._generation_job["ray_directions"]
        i_ray = self._generation_job["i_rays"]
        return directions[i_ray]

    def _setup(self):
        logger.info("Setting up data generation worker...")
        self._setup_triangle_property_maps()
        self._set_generation_flags()
        logger.info("Setup complete")
        self.set_as_ready()

    def _setup_triangle_property_maps(self):
        scene = load_track_mesh(self.track_mesh_path, self.modified_mesh_path)
        self._triangle_to_normal = get_triangle_to_normal_mapping(scene)
        self._triangle_to_id = get_triangle_to_semantic_id_mapping(scene)

    # TODO: What a nightmare, clean this up
    def _set_generation_flags(self):
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
