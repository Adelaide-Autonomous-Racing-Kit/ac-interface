import os
import tempfile

import pytest
from src.track_gen.track_gen import Monza
import trimesh


@pytest.mark.parametrize(
    "example_id, example_filename",
    [
        ("monza_test_track", "tracks/monza/monza_test_mesh.obj"),
    ],
)
@pytest.mark.slow
@pytest.mark.io
def test_monza_group_names(example_id: str, example_filename: str):
    track = Monza(example_filename)

    if example_id == "monza_test_track":
        assert track.group_names == {
            "pencnca",
            "asph",
            "pengrsd",
            "penasphb",
            "road",
            "concrete",
            "kerb",
            "penaspha",
            "sand",
            "wall",
            "grass",
            "penasphd",
            "pencncd",
            "illconc",
            "out",
            "curb",
        }

        # evaluating the wall mesh
        assert set(track.named_meshes.get("wall").keys()) == {"02WALL006"}
        assert len(track.named_meshes.get("wall")) == 1

        wall = track.named_meshes.get("wall").get("02WALL006")
        assert wall.vertices.shape == (219, 3)

        # evaluating the sand mesh(s)
        assert set(track.named_meshes.get("sand").keys()) == {"02SAND", "03SAND"}


# @pytest.mark.benchmark(group="obj-parser-methods")
# def test_obj_parse(benchmark):
#     example_id = "longer_wall"
#     example_file_input = longer_wall_example

#     obj_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
#     obj_file.write(example_file_input)
#     obj_file.close()

#     def f(filename):
#         _ = Monza(filename)
#         return True

#     benchmark(f, obj_file.name)
#     assert True


if __name__ == "__main__":
    pytest.main()
