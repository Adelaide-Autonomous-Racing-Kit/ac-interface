import cv2
from pathlib import Path


import numpy as np
import trimesh

# TODO: Dynamically import constants based on track
from src.tools.data_generation.tracks.monza import (
    COLOUR_LIST,
    MESH_NAME_TO_ID,
    TRAIN_ID_LIST,
)


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
