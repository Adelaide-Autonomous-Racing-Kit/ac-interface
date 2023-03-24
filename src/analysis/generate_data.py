import cv2
import os
import math
import shutil
from pathlib import Path
from typing import Dict, List

import numpy as np
import trimesh
from loguru import logger
from tqdm import tqdm

from src.utils.load import load_game_state, load_yaml
from src.utils.save import maybe_create_folders
from src.analysis.monza.constants import (
    GEOMETRIES_TO_REMOVE,
    COLOUR_LIST,
    MESH_NAME_TO_ID,
    TRAIN_ID_LIST,
    VERTEX_GROUPS_TO_MODIFY,
)


# TODO: finetune camera position, add multiprocessing
class DataGenerator:
    """
    Generates ground truth training data from recordings captured
        using the asseto corsa interface. Currently generates
        semantic segmentation maps, normal maps and depth maps.
        The depth and normal maps are scaled for visualisation.
    """

    def __init__(self, configuration_path: str):
        self._config = load_yaml(configuration_path)
        self.__setup()

    def __setup(self):
        self.__setup_fov()
        self.__setup_folders()
        self.__setup_scene()
        self.__setup_collision_mesh()

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
        return self._ray_intersections[2]

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
            self._save_gorund_truth_data(record)

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

    def _save_gorund_truth_data(self, record_number: str):
        self._adjust_camera(record_number)
        self._update_ray_intersections()
        colour_map, id_map = self._generate_semantic_map()
        depth_map = self._generate_depth_map()
        normal_map = self._generate_normal_map()
        self._save_colour_map(record_number, colour_map)
        self._save_segmentation_map(record_number, id_map)
        self._save_depth_map(record_number, depth_map)
        self._save_normal_map(record_number, normal_map)
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
        return self._mesh.intersects_location(origins, directions, False)

    def _generate_semantic_map(self):
        i_tri = np.copy(self._i_triangles)
        i_tri[i_tri != -1] = self._triangle_ids[i_tri[i_tri != -1]]
        pixel_ids = self._allocate_empty_frame()
        self._insert_values_into_image(i_tri, pixel_ids)
        visualised_map = np.array(COLOUR_LIST[pixel_ids], dtype=np.uint8)
        visualised_map = self._rgb_to_bgr(visualised_map)
        id_map = np.array(TRAIN_ID_LIST[pixel_ids], dtype=np.uint8)
        return id_map, visualised_map

    def _allocate_empty_frame(self, channels: int = 0) -> np.array:
        shape = self.image_size
        if channels > 0:
            shape = (*shape, channels)
        return np.zeros(shape, dtype=np.uint8)

    def _insert_values_into_image(self, values: np.array, image: np.array):
        image[self._pixels_to_rays[:, 0], self._pixels_to_rays[:, 1]] = values

    def _rgb_to_bgr(self, image: np.array) -> np.array:
        return image[:, :, ::-1]

    def _generate_depth_map(self):
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

    def _generate_normal_map(self):
        normals = self._triangle_normals[self._i_triangles]
        self._noramlise_values(normals)
        self._convert_to_uint8(normals)
        normal_map = self._allocate_empty_frame(channels=3)
        self._insert_values_into_image(normals, normal_map)
        return normal_map

    def _save_colour_map(self, record_number: str, colour_map: np.array):
        self._save_data(f"{record_number}-colour.png", colour_map)

    def _save_segmentation_map(self, record_number: str, ids_map: np.array):
        self._save_data(f"{record_number}-trainids.png", ids_map)

    def _save_depth_map(self, record_number: str, depth_map: np.array):
        self._save_data(f"{record_number}-depth.png", depth_map)

    def _save_normal_map(self, record_number: str, normal_map: np.array):
        self._save_data(f"{record_number}-normals.png", normal_map)

    def _save_data(self, filename: str, to_save: np.array):
        to_save = np.rot90(to_save)
        filepath = str(self.output_path.joinpath(filename))
        cv2.imwrite(filepath, to_save)

    def _copy_frame(self, record: str):
        source_path = self.recording_path.joinpath(record + ".jpeg")
        destination_path = self.output_path.joinpath(record + ".jpeg")
        shutil.copyfile(source_path, destination_path)

    def __setup_fov(self):
        fov_v = self._config["vertical_fov"]
        width, height = self.image_size
        focal_length = height / math.tan(math.radians(fov_v) / 2)
        fov_h = math.degrees(2 * math.atan(width / focal_length))
        self.fov = (fov_h, fov_v)

    def __setup_folders(self):
        maybe_create_folders(self.output_path)

    def __setup_scene(self):
        logger.info("Loading track mesh...")
        self._load_track_mesh()
        self._setup_triangle_to_semantic_id_mapping()
        self._setup_triangle_to_normal_mapping()
        logger.info("Track mesh loaded")

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


def main():
    root_path = Path(os.path.dirname(__file__))
    config_path = root_path.joinpath("monza/config.yaml")
    data_generator = DataGenerator(config_path)
    data_generator.generate_segmentation_data()


if __name__ == "__main__":
    main()
