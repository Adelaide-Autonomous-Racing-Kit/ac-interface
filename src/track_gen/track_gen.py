from collections import OrderedDict, defaultdict
import glob
import pathlib

TRACK_DATA = {"monza": "tracks/monza/2.obj"}


class Track:
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
        raw_group_names = set()
        with open(self.obj_filename, "r") as obj_file:
            for line in obj_file:
                if line.startswith("g "):
                    group_name = line.strip().split(" ")[1]
                    raw_group_names.add(group_name)
        return raw_group_names

    def _preprocess_obj_groupnames(self, group_names) -> dict:
        pass

    @property
    def get_walls(self):
        """Abstract method that returns a set of walls for the given track."""
        pass


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

    def _preprocess_obj_groupnames(self, group_names) -> dict:
        my_dict = defaultdict(set)

        for group_name in group_names:
            value = group_name
            s = group_name
            s = s.replace("MONZA-", "")
            s = "".join(filter(str.isalpha, s))
            key = s.lower()

            my_dict[key].add(value)

        return my_dict

    @property
    def group_names(self):
        return sorted(self.group_name_to_obj_group.keys())


if __name__ == "__main__":
    """
    Can you recommend any improvements to the clarity, efficiency, modularity and overall quality of the code?
    """
    track_names = map(pathlib.Path, glob.glob("tracks/*"))
    track_names = (track_name for track_name in track_names if track_name.is_dir())

    track_data = Monza()

    print(track_data.group_names)
