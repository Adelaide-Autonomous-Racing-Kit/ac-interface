import math
from typing import Dict, List

import trimesh


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
