import cv2
import math
import os
from pathlib import Path
from typing import Dict, List


import numpy as np
import trimesh

# TODO: Split utils file into data generator utils and ray caster utils
# TODO: Dynamically import constants based on track
from src.tools.data_generation.tracks.monza import (
    GEOMETRIES_TO_REMOVE,
    COLOUR_LIST,
    MESH_NAME_TO_ID,
    TRAIN_ID_LIST,
    VERTEX_GROUPS_TO_MODIFY,
)


def load_track_mesh(track_mesh: Path, modified_mesh: Path) -> trimesh.Scene:
    """
    Prepares a collision mesh for generating data from. Modifies and removes
        geometries specified in the track's constants.VERTEX_GROUPS_TO_MODIFY
    """
    preprocess_track_mesh(track_mesh, modified_mesh)
    scene = trimesh.load(modified_mesh)
    scene.delete_geometry(GEOMETRIES_TO_REMOVE)
    return scene


def preprocess_track_mesh(track_mesh: Path, modified_mesh: Path):
    """
    Changes the material of vertex groups specified in VERTEX_GROUPS_TO_MODIFY
        to physics. This material is ignored in the collision mesh used for
        ray casting so it a convenient way to remove vertex groups from the mesh.
    """
    is_modifying = False
    source_file = track_mesh.open("r")
    destination_file = modified_mesh.open("w")
    while line := source_file.readline():
        if "g " in line:
            is_modifying = False
        if is_vertex_group_to_modify(line):
            is_modifying = True
        if is_modifying and "usemtl" in line:
            destination_file.write("usemtl physics\n")
        else:
            destination_file.write(line)
    destination_file.close()
    source_file.close()


def is_vertex_group_to_modify(line: str) -> bool:
    """
    Returns True if the line contains any of the vertex group names
        specified in constants.VERTEX_GROUPS_TO_MODIFY
    """
    return any([name in line for name in VERTEX_GROUPS_TO_MODIFY])


def get_triangle_to_normal_mapping(scene: trimesh.Scene) -> np.array:
    """
    Returns a mapping between triangle indexes and the normal vector of
        that triangle's face.
    """
    normals, valid = trimesh.triangles.normals(scene.triangles)
    triangle_to_normal = np.zeros((valid.shape[0], 3), dtype=np.float32)
    triangle_to_normal[valid] = normals
    return triangle_to_normal


def get_triangle_to_semantic_id_mapping(scene: trimesh.Scene) -> np.array:
    """
    Returns a mapping between triangle indexes and the semantic ID of
        that triangle's geometry.
    """
    triangle_to_node = scene.triangles_node
    triangle_to_id = [MESH_NAME_TO_ID[name] for name in triangle_to_node]
    return np.asarray(triangle_to_id, dtype=np.uint8)


def calculate_horizontal_fov(
    vertical_fov: float,
    width: int,
    height: int,
) -> float:
    """
    Given the camera's image plane height and width in pixels and vertical
        field of view in degree calculates and returns the camera's horizontal
        field of view in degrees
    """
    focal_length = height / math.tan(math.radians(vertical_fov) / 2)
    return math.degrees(2 * math.atan(width / focal_length))


def convert_scene_to_collision_mesh(
    scene: trimesh.Scene,
) -> trimesh.ray.ray_pyembree.RayMeshIntersector:
    """
    Concatenates all the geometry nodes in a scene into a single trimesh.Mesh
        object and instantiates a RayMeshIntersector with it. The triangle
        indexes of the concatenated mesh align with the original scene, so
        collisions returned my the mesh intersector and be used index the scene
        which they are made from.
    """
    meshes = [mesh for mesh in scene.geometry.values()]
    mesh = trimesh.util.concatenate(meshes)
    return trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)


# TODO: Finetune camera pose base on car data
def get_camera_rotation(state: Dict) -> List[float]:
    """
    From a game capture state dictionary extract the camera pose's rotation
    """
    angles = [state["pitch"], -(state["heading"] + math.pi), state["roll"]]
    return angles


def get_camera_location(state: Dict) -> List[float]:
    """
    From a game capture state dictionary extract the camera pose's location
    """
    location = [
        state["ego_location_x"],
        state["ego_location_y"] + state["centre_of_gravity_height"],
        state["ego_location_z"],
    ]
    return location


def get_semantic_training_data(pixel_ids: np.array) -> np.array:
    id_map = np.array(TRAIN_ID_LIST[pixel_ids], dtype=np.uint8)
    return id_map


def get_visualised_semantics(pixel_ids: np.array) -> np.array:
    visualised_map = np.array(COLOUR_LIST[pixel_ids], dtype=np.uint8)
    visualised_map = rgb_to_bgr(visualised_map)
    return visualised_map


def rgb_to_bgr(image: np.array) -> np.array:
    return image[:, :, ::-1]


def noramlise_values(values: np.array) -> np.array:
    values -= values.min()
    values /= values.ptp()


def reverse_sign_of_values(values: np.array):
    values -= 1
    values *= -1


def convert_to_uint8(values) -> np.array:
    values *= 255
    values.astype(np.uint8, copy=False)


def allocate_empty_frame(
    width: int,
    height: int,
    channels: int = 0,
) -> np.array:
    shape = (width, height)
    if channels > 0:
        shape = (*shape, channels)
    return np.zeros(shape, dtype=np.uint8)


def calculate_depth(hit_to_camera: np.array, directions: np.array) -> np.array:
    return trimesh.util.diagonal_dot(hit_to_camera, directions)


def save_image(to_save: np.array, filepath: Path, flipud: bool):
    to_save = np.rot90(to_save)
    if flipud:
        to_save = np.flipud(to_save)
    cv2.imwrite(str(filepath), to_save)


def get_sample_list(recording_path: Path) -> List[str]:
    filenames = os.listdir(recording_path)
    samples = filter_for_game_state_files(filenames)
    return sort_records(samples)


def filter_for_game_state_files(filenames: List[str]) -> List[str]:
    return [record[:-4] for record in filenames if record[-4:] == ".bin"]


def sort_records(filenames: List[str]) -> List[str]:
    return sorted(filenames, key=lambda x: int(x))
