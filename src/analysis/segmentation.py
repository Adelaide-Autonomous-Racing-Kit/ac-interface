import os
import math

import trimesh
from loguru import logger

from src.utils.load import load_game_state
from src.track_gen.track_gen import Monza

TRACK_MESH_PATH = "../tracks/monza/visual_mesh.obj"
RECORDED_DATA_PATH = "../recordings/monza_audi_r8_lms_1/"
RECORD_FILE = "3675.bin"
RECORD_FILE = "3325.bin"
RECORD_FILE = "4170.bin"


def get_scene():
    # track.scene is a list of trimesh objects
    track = Monza(TRACK_MESH_PATH)
    all_meshes = []
    logger.info(f"{track.named_meshes.keys()}")
    for name in track.named_meshes.keys():
        if not name == "monzal" or not "tree" in name:
            meshes = track.named_meshes[name]
            meshes = [mesh for mesh in meshes.values()]
            all_meshes.extend(meshes)
    all_meshes = trimesh.util.concatenate(all_meshes)
    return all_meshes.scene()


def set_angles_and_show(scene, angles):
    state = load_game_state(os.path.join(RECORDED_DATA_PATH, RECORD_FILE))
    # angles = (state["pitch"], state["heading"] + math.pi, state["roll"])
    logger.info((state["pitch"], state["heading"], state["roll"]))
    distance = -0.5
    center = (
        state["ego_location_x"],
        state["ego_location_y"] + state["centre_of_gravity_height"],
        state["ego_location_z"],
    )
    fov = (91, 60)
    resolution = (1920, 1080)
    scene.set_camera(angles, distance, center, resolution, fov)
    scene.show()


if __name__ == "__main__":
    for file in sorted(
        os.listdir(RECORDED_DATA_PATH), key=lambda x: int(x.split(".")[0])
    ):
        if ".bin" in file:
            state = load_game_state(os.path.join(RECORDED_DATA_PATH, file))
            logger.info(
                f"File: {file}, X: {state['ego_location_x']}, Z: {state['ego_location_z']}"
            )
