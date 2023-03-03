import cv2
import os
import math
import numpy as np
from pathlib import Path
from typing import List

import trimesh
from loguru import logger

from src.utils.load import load_game_state
from src.track_gen.track_gen import Monza

TRACK_MESH_PATH = Path.home().joinpath(Path("Documents/tracks/monza/visual_mesh.obj"))
RECORDED_DATA_PATH = Path.home().joinpath(
    Path("Documents/recordings/monza_audi_r8_lms_1/")
)
RECORD_FILE = "3675.bin"
RECORD_FILE = "3325.bin"
RECORD_FILE = "4170.bin"
RECORD_FILE = "5090.bin"


def get_scene():
    scene = trimesh.Scene()

    track = Monza(TRACK_MESH_PATH)
    logger.info(f"{track.named_meshes.keys()}")
    for name in track.named_meshes.keys():
        meshes = track.named_meshes[name]
        meshes = [mesh for mesh in meshes.values()]
        combined_mesh = trimesh.util.concatenate(meshes)
        scene.add_geometry(
            combined_mesh,
            node_name=name,
        )

    logger.info(len(scene.geometry))
    return scene


def setup_camera(scene, state_filename: str):
    state = load_game_state(os.path.join(RECORDED_DATA_PATH, state_filename + ".bin"))
    angles = [state["pitch"], state["heading"], state["roll"]]
    logger.info(angles)
    angles[1] = angles[1] + math.pi
    logger.info(angles)
    distance = 0.0
    center = (
        state["ego_location_x"],
        state["ego_location_y"] + state["centre_of_gravity_height"],
        state["ego_location_z"],
    )
    fov = (91, 60)
    resolution = (1920, 1080)
    scene.set_camera(angles, distance, center, resolution, fov)


def get_triangle_ray_intersections(scene) -> List[int]:
    mesh = trimesh.util.concatenate([mesh for mesh in scene.geometry.values()])
    ray_mesh_int = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)
    origins, vectors, _ = scene.camera_rays()
    tri_indexs = ray_mesh_int.intersects_first(origins, vectors)
    return scene.triangles_node[tri_indexs]


import matplotlib.cm as cm
import random


def make_colour_map(scene):
    names = [name for name in scene.triangles_node]
    cmap = cm.get_cmap("viridis")
    values = np.arange(len(names))
    # colours = cmap(values)
    # colour_map = {name: colour[:3] for name, colour in zip(names, colours)}
    colour_map = {
        name: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for name in names
    }
    logger.info(colour_map)
    return colour_map


def show_colour_map(scene):
    colour_map = make_colour_map(scene)
    pixel_geometry_names = get_triangle_ray_intersections(scene)
    to_plot = (
        np.array(
            [colour_map[pixel_name] for pixel_name in pixel_geometry_names]
        ).reshape(1920, 1080, 3)
        * 255
    )
    # to_plot = np.transpose(to_plot, (0, 1))

    to_plot = np.rot90(to_plot)
    # to_plot = np.flip(to_plot)
    to_plot = np.flipud(to_plot)
    to_plot = to_plot.astype(np.uint8)
    cv2.imshow("hello", to_plot)
    cv2.waitKey()


def main():
    scene = get_scene()
    setup_camera(scene, "5090")
    show_colour_map(scene)


if __name__ == "__main__":
    main()
