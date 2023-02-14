import os
import re
import pywavefront
import trimesh
import pathlib
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple, Union

TRACK_DATA = {"monza": "tracks/monza/2.obj"}


class Track(ABC):
    """Base class representing a track."""

    def __init__(self, obj_filename: pathlib.Path) -> None:
        """Initialize a Track object.

        Args:
            obj_filename (pathlib.Path): Path to the .obj file containing track data.
        """
        self.obj_filename = obj_filename
        self.scene = self._parse_obj_file(obj_filename)
        self.group_name_to_obj_group = self._preprocess_obj_groupnames(self.scene)

    def _parse_obj_file(self, file: pathlib.Path) -> pywavefront.Wavefront:
        """Parse obj file using pywavefront"""
        return pywavefront.Wavefront(
            file, strict=False, collect_faces=True, create_materials=True
        )

    def _preprocess_obj_groupnames(
        self, scene: pywavefront.Wavefront
    ) -> Dict[str, Set[str]]:
        """Sort all of the groupnames into class name and a set of unsanitised names"""
        result = {}
        for group_name in scene.meshes.keys():
            key = self._process_group_name(group_name)
            result[key] = result.get(key, set()).union({group_name})
        return result

    def _parse_named_mesh(
        self, class_name: set
    ) -> List[Dict[str, Union[str, Tuple[float, float, float]]]]:
        return {
            mesh_name: trimesh.Trimesh(vertices=self.scene.vertices, faces=mesh.faces)
            for mesh_name, mesh in self.scene.meshes.items()
            if mesh_name in self.group_name_to_obj_group.get(class_name, {})
        }


class Monza(Track):
    """Class representing the Monza track."""

    def __init__(
        self, obj_filename: pathlib.Path = pathlib.Path(TRACK_DATA.get("monza"))
    ) -> None:
        """Initialize a Monza object.

        Args:
            obj_filename (pathlib.Path): Path to the .obj file containing Monza track data.
        """
        super().__init__(obj_filename)

        self.scene = self._parse_obj_file(obj_filename)
        self.walls = self._parse_named_mesh("wall")

    @staticmethod
    def _process_group_name(s: str) -> str:
        s = s.replace("MONZA-", "")
        s = "".join(filter(str.isalpha, s))
        return s.lower()

    @property
    def group_names(self) -> set:
        return set(self.group_name_to_obj_group.keys())


if __name__ == "__main__":
    #     # file = "tracks/monza/2_object_groups.obj"
    file = "tracks/monza/2_vertex_groups.obj"

    monza_data = Monza(file)
