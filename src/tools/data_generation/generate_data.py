import ctypes
import cv2
import os
import math
import shutil
import time
import multiprocessing as mp
from pathlib import Path
from threading import Thread
from typing import Dict, List

import numpy as np
import trimesh
from loguru import logger
from tqdm import tqdm

from src.utils.load import load_game_state, load_yaml
from src.utils.save import maybe_create_folders
from src.tools.data_generation.monza.constants import (
    GEOMETRIES_TO_REMOVE,
    COLOUR_LIST,
    MESH_NAME_TO_ID,
    TRAIN_ID_LIST,
    VERTEX_GROUPS_TO_MODIFY,
)


# TODO: finetune camera position, add multiprocessing,
#   dynamically import constants based on track
class DataGenerator(mp.Process):
    """
    Generates ground truth training data from recordings captured
        using the asseto corsa interface. Currently generates
        semantic segmentation maps, normal maps and depth maps.
        The depth and normal maps are scaled for visualisation.
    """

    def __init__(
        self,
        configuration_path: str,
        shared_queue: mp.Queue,
        shared_is_done: mp.Value,
        shared_is_ready: mp.Value,
        shared_n_done: mp.Value,
    ):
        super().__init__()
        self._shared_is_done = shared_is_done
        self._shared_queue = shared_queue
        self._shared_n_done = shared_n_done
        self._shared_is_ready = shared_is_ready
        self._config = load_yaml(configuration_path)

    @property
    def track_mesh_path(self) -> Path:
        return Path(self._config["track_mesh_path"])

    @property
    def modified_mesh_path(self) -> Path:
        return self.track_mesh_path.parent / "tmp.obj"

    @property
    def recording_path(self) -> Path:
        return Path(self._config["recorded_data_path"])

    @property
    def output_path(self) -> Path:
        return Path(self._config["output_path"])

    @property
    def image_size(self) -> List[int]:
        return self._config["image_size"]

    @property
    def _i_rays(self) -> np.array:
        """
        Index for each ray cast by camera pixels
        """
        return self._ray_intersections[1]

    @property
    def _i_triangles(self) -> np.array:
        """
        Index of each triangle hit by a given ray
        """
        if self._is_generating_depth:
            return self._ray_intersections[2]
        return self._ray_intersections

    @property
    def _locations(self) -> np.array:
        """
        3D points where rays hit a triangle
        """
        return self._ray_intersections[0]

    @property
    def _pixels(self) -> np.array:
        """
        Mapping from image coordinates to rays
        """
        return self._camera_rays[2]

    @property
    def _ray_origins(self) -> np.array:
        """
        Origin of camera ray for each pixel
        """
        return self._camera_rays[0]

    @property
    def _ray_directions(self) -> np.array:
        """
        Direction of camera ray for each pixel
        """
        return self._camera_rays[1]

    @property
    def _triangle_nodes(self) -> np.array:
        """
        Mapping fron triangle index to scene graph node ID
        """
        return self._scene.triangle_nodes

    def run(self):
        """
        Called on DataGenerator.start()
        """
        self.__setup()
        self.is_running = True
        while self.is_running:
            record_number = self._shared_queue.get()
            self.save_gorund_truth_data(record_number)
            with self._shared_n_done.get_lock():
                self._shared_n_done.value += 1
            if self._shared_queue.empty():
                break
        self._shared_is_done = True

    def stop(self):
        """
        Called to end the processes waiting on the shared queue
        """
        self.is_running = False

    def generate_segmentation_data(self):
        """
        Run through each of the records specifed in the configuration
            file. For each it generates and saves the following:
            - Visualised segmentation map
            - Segmentation map with train ids
            - Visualised normal map of the scene
            - Visualised depth map of the scene
            It also copies the original frame captured to the output
            folder to be used as input in the training dataset.
        """
        for record in tqdm(self._get_subsample()):
            self.save_gorund_truth_data(record)

    def save_gorund_truth_data(self, record_number: str):
        self._adjust_camera(record_number)
        self._update_ray_intersections()
        if self._is_generating_segmentation:
            self._generate_semantic_segmentation_data(record_number)
        if self._is_generating_depth:
            self._generate_depth_map(record_number)
        if self._is_generating_normals:
            self._generate_normal_map(record_number)
        self._copy_frame(record_number)

    def _adjust_camera(self, state_filename: str):
        game_state_path = self.recording_path.joinpath(state_filename + ".bin")
        state = load_game_state(game_state_path)
        self._scene.set_camera(
            angles=self._get_camera_rotation(state),
            center=self._get_camera_location(state),
            resolution=self.image_size,
            distance=0.0,
            fov=self.fov,
        )
        self._set_camera_rays()

    def _set_camera_rays(self):
        # (origin, direction unit vector, pixel each ray belongs to)
        self._camera_rays = self._scene.camera_rays()

    def _get_camera_rotation(self, state: Dict) -> List[float]:
        angles = [state["pitch"], -(state["heading"] + math.pi), state["roll"]]
        return angles

    def _get_camera_location(self, state: Dict) -> List[float]:
        location = [
            state["ego_location_x"],
            state["ego_location_y"] + state["centre_of_gravity_height"],
            state["ego_location_z"],
        ]
        return location

    def _update_ray_intersections(self):
        self._ray_intersections = self._cast_camera_rays()
        self._pixels_to_rays = self._pixels[self._i_rays]

    def _cast_camera_rays(self):
        origins, directions = self._ray_origins, self._ray_directions
        if not self._is_generating_depth:
            return self._mesh.intersects_first(origins, directions)
        return self._mesh.intersects_location(origins, directions, False)

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
            pixel_ids = self._allocate_empty_frame()
            self._insert_values_into_image(i_tri, pixel_ids)
        else:
            pixel_ids = i_tri.reshape(self.image_size)
        return pixel_ids

    def _generate_visualised_semantics(
        self,
        record_number: str,
        pixel_ids: np.array,
    ):
        visualised_map = self._get_visualied_semantics(pixel_ids)
        self._save_colour_map(record_number, visualised_map)

    def _get_visualied_semantics(self, pixel_ids: np.array) -> np.array:
        visualised_map = np.array(COLOUR_LIST[pixel_ids], dtype=np.uint8)
        visualised_map = self._rgb_to_bgr(visualised_map)
        return visualised_map

    def _rgb_to_bgr(self, image: np.array) -> np.array:
        return image[:, :, ::-1]

    def _save_colour_map(self, record_number: str, colour_map: np.array):
        self._save_data(f"{record_number}-colour.png", colour_map)

    def _generate_semantic_training_data(
        self,
        record_number: str,
        pixel_ids: np.array,
    ):
        id_map = self._get_semantic_training_data(pixel_ids)
        self._save_segmentation_map(record_number, id_map)

    def _get_semantic_training_data(self, pixel_ids: np.array) -> np.array:
        id_map = np.array(TRAIN_ID_LIST[pixel_ids], dtype=np.uint8)
        return id_map

    def _save_segmentation_map(self, record_number: str, ids_map: np.array):
        self._save_data(f"{record_number}-trainids.png", ids_map)

    def _allocate_empty_frame(self, channels: int = 0) -> np.array:
        shape = self.image_size
        if channels > 0:
            shape = (*shape, channels)
        return np.zeros(shape, dtype=np.uint8)

    def _insert_values_into_image(self, values: np.array, image: np.array):
        image[self._pixels_to_rays[:, 0], self._pixels_to_rays[:, 1]] = values

    def _generate_depth_map(self, record_number: str):
        depth_map = self._get_depth_map()
        self._save_depth_map(record_number, depth_map)

    def _get_depth_map(self):
        depth = self._calculate_depth()
        self._noramlise_values(depth)
        self._reverse_sign_of_values(depth)
        self._convert_to_uint8(depth)
        depth_map = self._allocate_empty_frame()
        self._insert_values_into_image(depth, depth_map)
        return depth_map

    def _calculate_depth(self) -> np.array:
        hit_to_camera = self._locations - self._ray_origins[0]
        direction = self._ray_directions[self._i_rays]
        return trimesh.util.diagonal_dot(hit_to_camera, direction)

    def _noramlise_values(self, values: np.array) -> np.array:
        values -= values.min()
        values /= values.ptp()

    def _reverse_sign_of_values(self, values: np.array):
        values -= 1
        values *= -1

    def _convert_to_uint8(self, values) -> np.array:
        values *= 255
        values.astype(np.uint8, copy=False)

    def _generate_normal_map(self, record_number: str):
        normal_map = self._get_normal_map()
        self._save_normal_map(record_number, normal_map)

    def _get_normal_map(self):
        normals = self._triangle_normals[self._i_triangles]
        self._noramlise_values(normals)
        self._convert_to_uint8(normals)
        if self._is_generating_depth:
            normal_map = self._allocate_empty_frame(channels=3)
            self._insert_values_into_image(normals, normal_map)
        else:
            normal_map = normals.reshape((*self.image_size, 3))
        return normal_map

    def _save_depth_map(self, record_number: str, depth_map: np.array):
        self._save_data(f"{record_number}-depth.png", depth_map)

    def _save_normal_map(self, record_number: str, normal_map: np.array):
        self._save_data(f"{record_number}-normals.png", normal_map)

    def _save_data(self, filename: str, to_save: np.array):
        to_save = np.rot90(to_save)
        if not self._is_generating_depth:
            to_save = np.flipud(to_save)
        filepath = str(self.output_path.joinpath(filename))
        cv2.imwrite(filepath, to_save)

    def _copy_frame(self, record: str):
        source_path = self.recording_path.joinpath(record + ".jpeg")
        destination_path = self.output_path.joinpath(record + ".jpeg")
        shutil.copyfile(source_path, destination_path)

    def __setup(self):
        logger.info("Setting up data generator...")
        self.__setup_data_generators()
        self.__setup_fov()
        self.__setup_folders()
        self.__setup_scene()
        self.__setup_collision_mesh()
        logger.info("Setup complete")
        self._shared_is_ready.value = True

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

    def __setup_fov(self):
        fov_v = self._config["vertical_fov"]
        width, height = self.image_size
        focal_length = height / math.tan(math.radians(fov_v) / 2)
        fov_h = math.degrees(2 * math.atan(width / focal_length))
        self.fov = (fov_h, fov_v)

    def __setup_folders(self):
        maybe_create_folders(self.output_path)

    def __setup_scene(self):
        self._load_track_mesh()
        self._setup_triangle_to_semantic_id_mapping()
        self._setup_triangle_to_normal_mapping()

    def _load_track_mesh(self):
        self._preprocess_track_mesh()
        scene = trimesh.load(self.modified_mesh_path)
        scene.delete_geometry(GEOMETRIES_TO_REMOVE)
        self._scene = scene

    def _setup_triangle_to_semantic_id_mapping(self):
        triangles_nodes = self._scene.triangles_node
        triangles_ids = [MESH_NAME_TO_ID[name] for name in triangles_nodes]
        self._triangle_ids = np.asarray(triangles_ids, dtype=np.uint8)

    def _setup_triangle_to_normal_mapping(self):
        normals, valid = trimesh.triangles.normals(self._scene.triangles)
        normals_cache = np.zeros((valid.shape[0], 3), dtype=np.float32)
        normals_cache[valid] = normals
        self._triangle_normals = normals_cache

    def _preprocess_track_mesh(self):
        is_modifying = False
        source_file = self.track_mesh_path.open("r")
        destination_file = self.modified_mesh_path.open("w")
        while line := source_file.readline():
            if "g " in line:
                is_modifying = False
            if self._is_vertex_group_to_modify(line):
                is_modifying = True
            if is_modifying and "usemtl" in line:
                destination_file.write("usemtl physics\n")
            else:
                destination_file.write(line)
        destination_file.close()
        source_file.close()

    def _is_vertex_group_to_modify(self, line: str) -> bool:
        return any([name in line for name in VERTEX_GROUPS_TO_MODIFY])

    def __setup_collision_mesh(self):
        meshes = [mesh for mesh in self._scene.geometry.values()]
        mesh = trimesh.util.concatenate(meshes)
        self._mesh = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)


class MultiprocessDataGenerator:
    def __init__(self, configuration_path: str):
        self._config = load_yaml(configuration_path)
        self._n_workers = self._config["n_workers"]
        self._log_configuration()
        self.__setup_workers(configuration_path)
    
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
            worker = DataGenerator(
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
        Populates the queue with work and starts consumers
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
