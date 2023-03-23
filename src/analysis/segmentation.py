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

    def __setup_fov(self):
        fov_v = self._config["vertical_fov"]
        width, height = self.image_size
        focal_length = height / math.tan(math.radians(fov_v) / 2)
        fov_h = math.degrees(2 * math.atan(width / focal_length))
        self.fov = (fov_h, fov_v)

    def __setup_folders(self):
        maybe_create_folders(self.output_path)

    def __setup_scene(self):
        logger.info("Loading track meshes...")
        self._preprocess_track_mesh()
        scene = trimesh.load(self.modified_mesh_path)
        scene.delete_geometry(GEOMETRIES_TO_REMOVE)
        scene.triangles_to_ids = np.asarray(
            [MESH_NAME_TO_ID[name] for name in scene.triangles_node]
        )
        self._scene = scene
        logger.info("Track mesh loaded")

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

    def generate_segmentation_data(self):
        for record in tqdm(self._get_subsample()):
            self._save_gorund_truth_data(record)

    def _get_subsample(self):
        start = self._config["start_at_sample"]
        end = self._config["finish_at_sample"]
        interval = self._config["sample_every"]
        return self._get_sample_list()[start:end:interval]

    def _get_sample_list(self) -> List[str]:
        samples = [
            record[:-4]
            for record in os.listdir(self.recording_path)
            if record[-4:] == ".bin"
        ]
        return sorted(samples, key=lambda x: int(x))

    def _save_gorund_truth_data(self, record_number: str):
        self._adjust_camera(record_number)
        pixel_ids, depth, normals = self._get_triangle_ray_intersections()
        self._save_colour_map(record_number, pixel_ids)
        self._save_segmentation_map(record_number, pixel_ids)
        self._save_depth_map(record_number, depth)
        self._save_normal_map(record_number, normals)
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

    def _get_triangle_ray_intersections(self) -> List[int]:
        origins, vectors, pixels = self._scene.camera_rays()
        points, ray_indices, tri_indices = self._mesh.intersects_location(
            origins, vectors, multiple_hits=False
        )
        pixel_ray = pixels[ray_indices]
        # Normal Map
        normals, _ = trimesh.triangles.normals(
            self._scene.triangles[tri_indices]
        )
        normal_map = self._allocate_empty_frame(channels=3)
        normals = (normals - normals.min()) / normals.ptp()
        normals = (normals * 255).round().astype(np.uint8)
        normal_map[pixel_ray[:, 0], pixel_ray[:, 1]] = normals
        # Depth Map
        depth = trimesh.util.diagonal_dot(
            points - origins[0], vectors[ray_indices]
        )
        depth_float = abs(((depth - depth.min()) / depth.ptp()) - 1)
        depth_int = (depth_float * 255).round().astype(np.uint8)
        depth_map = self._allocate_empty_frame()
        depth_map[pixel_ray[:, 0], pixel_ray[:, 1]] = depth_int
        # Semantic Lables
        tri_indices[tri_indices != -1] = self._scene.triangles_to_ids[
            tri_indices[tri_indices != -1]
        ]
        pixel_ids = self._allocate_empty_frame()
        pixel_ids[pixel_ray[:, 0], pixel_ray[:, 1]] = tri_indices
        return pixel_ids, depth_map, normal_map

    def _allocate_empty_frame(self, channels: int = 0) -> np.array:
        shape = self.image_size
        if channels > 0:
            shape = (*self.image_size, channels)
        return np.zeros(shape, dtype=np.uint8)

    def _save_colour_map(self, record_number: str, pixel_ids: np.array):
        visualised_map = np.array(COLOUR_LIST[pixel_ids], dtype=np.uint8)
        visualised_map = visualised_map.reshape(*self.image_size, 3)
        visualised_map = cv2.cvtColor(visualised_map, cv2.COLOR_RGB2BGR)
        visualised_map = np.rot90(visualised_map)
        filepath = self.output_path.joinpath(f"{record_number}-colour.png")
        cv2.imwrite(str(filepath), visualised_map)

    def _save_segmentation_map(self, record_number: str, pixel_ids: np.array):
        segmentation_map = np.array(TRAIN_ID_LIST[pixel_ids], dtype=np.uint8)
        segmentation_map = segmentation_map.reshape(*self.image_size)
        segmentation_map = np.rot90(segmentation_map)
        filepath = self.output_path.joinpath(f"{record_number}-trainids.png")
        cv2.imwrite(str(filepath), segmentation_map)

    def _save_depth_map(self, record_number: str, depth_map: np.array):
        depth_map = np.rot90(depth_map)
        filepath = self.output_path.joinpath(f"{record_number}-depth.png")
        cv2.imwrite(str(filepath), depth_map)

    def _save_normal_map(self, record_number: str, normal_map: np.array):
        normal_map = np.rot90(normal_map)
        filepath = self.output_path.joinpath(f"{record_number}-normals.png")
        cv2.imwrite(str(filepath), normal_map)

    def _copy_frame(self, record: str):
        source_path = self.recording_path.joinpath(record + ".jpeg")
        destination_path = self.output_path.joinpath(record + ".jpeg")
        shutil.copyfile(source_path, destination_path)


def main():
    root_path = Path(os.path.dirname(__file__))
    config_path = root_path.joinpath("monza/config.yaml")
    data_generator = DataGenerator(config_path)
    data_generator.generate_segmentation_data()


if __name__ == "__main__":
    main()
