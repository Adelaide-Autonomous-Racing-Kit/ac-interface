import os
import re
import pathlib
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Union

TRACK_DATA = {"monza": "tracks/monza/2.obj"}


class Track(ABC):
    """Base class representing a track."""

    def __init__(self, obj_filename: pathlib.Path) -> None:
        """Initialize a Track object.

        Args:
            obj_filename (pathlib.Path): Path to the .obj file containing track data.
        """
        self.obj_filename = obj_filename
        self._raw_group_names = self.parse_obj_file()
        self.group_name_to_obj_group = self._preprocess_obj_groupnames(
            self._raw_group_names
        )

    def parse_obj_file(self):
        """Parse the .obj file and return a set of all group names found.

        Returns:
            set: A set of all group names found in the .obj file.
        """
        pattern = re.compile(r"g (.*)")
        with open(self.obj_filename, "r") as obj_file:
            return {
                match.group(1)
                for match in (pattern.match(line) for line in obj_file)
                if match
            }

    def _preprocess_obj_groupnames(self, group_names) -> dict:
        result = {}
        for group_name in group_names:
            key = self._process_group_name(group_name)
            result[key] = result.get(key, set()).union({group_name})
        return result


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
        self.wall_group_names = self.group_name_to_obj_group.get("wall", {})
        self.walls = self._parse_walls(obj_filename)

    @staticmethod
    def _process_group_name(s: str) -> str:
        print(s)
        s = s.replace("MONZA-", "")
        s = "".join(filter(str.isalpha, s))
        return s.lower()

    @property
    def group_names(self) -> set:
        return set(self.group_name_to_obj_group.keys())

    def _parse_walls(
        self, obj_filename: pathlib.Path
    ) -> List[Dict[str, Union[str, Tuple[float, float, float]]]]:
        """Parses the .obj file for wall groups.

        Args:
            obj_filename (pathlib.Path): Path to the .obj file containing wall data.

        Returns:
            list: A list of dictionaries, each representing a wall group and its vertices.
        """
        current_group_name = None
        current_vertices = []
        walls = []
        with open(self.obj_filename, "r") as obj_file:
            for line in obj_file:
                if line.startswith("g "):
                    if current_group_name and current_vertices:
                        if self._process_group_name(current_group_name) == "wall":
                            walls.append(
                                {
                                    "group_name": current_group_name,
                                    "vertices": current_vertices,
                                }
                            )
                    current_group_name = line.strip().split(" ")[1]
                    current_vertices = []
                elif line.startswith("v "):
                    vertex = tuple(map(float, line.strip().split(" ")[1:]))
                    current_vertices.append(vertex)
        if current_group_name and current_vertices:
            if self._process_group_name(current_group_name) == "wall":
                walls.append(
                    {"group_name": current_group_name, "vertices": current_vertices}
                )

        return walls
