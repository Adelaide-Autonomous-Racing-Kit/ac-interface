from abc import ABC, abstractmethod
import os
import pathlib
import re
from typing import Dict, List, Set, Tuple, Union

import pywavefront
import trimesh

TRACK_DATA = {
    "monza": "tracks/monza/physics_mesh_object_groups.obj",  # 2.obj
    "spa": "tracks/spa/physics_mesh_object_groups.obj",  # 3.obj
}


def flatten(unflattened_list: list) -> list:
    return [item for sublist in unflattened_list for item in sublist]


class ACOObjParser(pywavefront.ObjParser):
    def parse_g(self):
        # do nothing with this info
        self.next_line()

    def parse_s(self):
        # do nothing with this info
        self.next_line()


class ACWavefront(pywavefront.Wavefront):
    parser_cls = ACOObjParser


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

        self.named_meshes = {
            name: self._parse_named_mesh(name)
            for name in self.group_name_to_obj_group.keys()
        }

    def _parse_obj_file(self, file: pathlib.Path) -> pywavefront.Wavefront:
        """Parse obj file using pywavefront"""
        return ACWavefront(
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
        named_meshes = {}
        for mesh_name, mesh in self.scene.meshes.items():
            if mesh_name in self.group_name_to_obj_group.get(class_name, {}):
                # only pass the necessary vertices to trimesh, otherwise it stores everything!
                mesh_indices = flatten(mesh.faces)
                min_idx, max_idx = min(mesh_indices), max(mesh_indices)
                vertices_needed_for_mesh = self.scene.vertices[min_idx : max_idx + 1]

                # zero index indices
                new_mesh_indices = [
                    list(map(lambda val: val - min_idx, arr)) for arr in mesh.faces
                ]

                named_meshes[mesh_name] = trimesh.Trimesh(
                    process=False,
                    vertices=vertices_needed_for_mesh,
                    faces=new_mesh_indices,
                    cache=True,
                )

        return named_meshes


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

    @staticmethod
    def _process_group_name(s: str) -> str:
        s = s.replace("MONZA-", "")
        s = "".join(filter(str.isalpha, s))
        return s.lower()

    @property
    def group_names(self) -> set:
        return set(self.group_name_to_obj_group.keys())


class Spa(Track):
    """Class representing the Spa track."""

    def __init__(
        self, obj_filename: pathlib.Path = pathlib.Path(TRACK_DATA.get("spa"))
    ) -> None:
        """Initialize a Spa object.

        Args:
            obj_filename (pathlib.Path): Path to the .obj file containing Spa track data.
        """
        super().__init__(obj_filename)

        self.scene = self._parse_obj_file(obj_filename)

    @staticmethod
    def _process_group_name(s: str) -> str:
        s = "".join(filter(str.isalpha, s))
        s = s.replace("SPA", "")
        s = s.replace("BLACK", "")
        return s.lower()

    @property
    def group_names(self) -> set:
        return set(self.group_name_to_obj_group.keys())


if __name__ == "__main__":
    file = "tracks/spa/physics_mesh_object_groups.obj"
    spa_data = Spa(file)

    print(spa_data.named_meshes.keys())

    for k, v in spa_data.named_meshes.get("sand").items():
        print(k, v)
