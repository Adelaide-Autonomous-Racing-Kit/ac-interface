import cv2
import os
import math
import numpy as np
import time
from pathlib import Path
from typing import List

import trimesh
from loguru import logger
from tqdm import tqdm

from src.utils.load import load_game_state
from src.track_gen.track_gen import Monza
from src.analysis.monza.constants import (
    MESH_NAME_TO_SEMANTIC_CLASS,
    COLOUR_LIST,
    MESH_NAME_TO_ID,
)

TRACK_MESH_PATH = Path.home().joinpath(Path("Documents/tracks/monza/visual_mesh.obj"))
RECORDED_DATA_PATH = Path.home().joinpath(
    Path("Documents/recordings/monza_audi_r8_lms_1/")
)


class SegmentationGenerator:
    def __init__(self):
        self.__setup_scene()
        self.__setup_collision_mesh()

    def __setup_scene(self):
        logger.info("Loading track meshes...")
        scene = trimesh.Scene()
        track = Monza(TRACK_MESH_PATH)
        for name in MESH_NAME_TO_SEMANTIC_CLASS.keys():
            meshes = track.named_meshes[name]
            meshes = [mesh for mesh in meshes.values()]
            combined_mesh = trimesh.util.concatenate(meshes)
            scene.add_geometry(
                combined_mesh,
                node_name=name,
            )
        scene.triangles_to_ids = np.asarray(
            [MESH_NAME_TO_ID[name] for name in scene.triangles_node]
        )
        self._scene = scene
        logger.info("Track mesh loaded")

    def __setup_collision_mesh(self):
        meshes = [mesh for mesh in self._scene.geometry.values()]
        mesh = trimesh.util.concatenate(meshes)
        self._mesh = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)

    def adjust_camera(self, state_filename: str):
        state = load_game_state(
            os.path.join(RECORDED_DATA_PATH, state_filename + ".bin")
        )
        angles = [state["pitch"], state["heading"], state["roll"]]
        angles[1] = -(angles[1] + math.pi)
        distance = 0.0
        center = [
            state["ego_location_x"],
            state["ego_location_y"] + state["centre_of_gravity_height"],
            state["ego_location_z"],
        ]
        fov = (91, 60)
        resolution = (1920, 1080)
        self._scene.set_camera(angles, distance, center, resolution, fov)

    def _get_triangle_ray_intersections(self) -> List[int]:
        origins, vectors, _ = self._scene.camera_rays()
        tri_indexes = self._mesh.intersects_first(origins, vectors)
        tri_indexes[tri_indexes != -1] = self._scene.triangles_to_ids[
            tri_indexes[tri_indexes != -1]
        ]
        return tri_indexes

    def save_colour_map(self, record_number: str):
        pixel_ids = self._get_triangle_ray_intersections()
        to_plot = np.array(
            COLOUR_LIST[pixel_ids],
            dtype=np.uint8,
        ).reshape(1920, 1080, 3)
        to_plot = cv2.cvtColor(to_plot, cv2.COLOR_RGB2BGR)
        to_plot = np.rot90(to_plot)
        to_plot = np.flipud(to_plot)
        cv2.imwrite(
            os.path.join(RECORDED_DATA_PATH, f"{record_number}-colour.png"),
            to_plot,
        )


def main():
    segmentation_generator = SegmentationGenerator()
    records = sorted(
        [
            record[:-4]
            for record in os.listdir(RECORDED_DATA_PATH)
            if record[-3:] == "bin"
        ],
        key=lambda x: int(x),
    )
    for record in tqdm(records):
        segmentation_generator.adjust_camera(record)
        segmentation_generator.save_colour_map(record)


if __name__ == "__main__":
    main()
