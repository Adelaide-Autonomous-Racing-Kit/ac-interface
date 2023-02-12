import os
import tempfile
import pytest
from src.track_gen.track_gen import Monza

wall_example = """g 09WALL002
v -216.9998 -9.689583 748.7813
v -219.1955 -6.713692 731.4688
v -216.9998 -6.689583 748.7813
vn 0.9920538 7.703942E-18 -0.1258149
vn 0.9920538 7.703942E-18 -0.1258149
vn 0.9920537 7.703942E-18 -0.1258149
vt 0.1162915 1.063541
vt 0.1162492 1.063478
vt 0.1162915 1.063541
"""

track_example = """g 14MONZA-ASPH6548
v 115.2428 -5.9782 -76.23053
v 115.4201 -5.975914 -76.90054
v 115.2369 -5.975147 -76.57008
v 115.1416 -5.781893 -107.1492
vn 0.01743671 0.999808 0.008936513
vn 0.01834496 0.9997935 0.008746906
vn 0.01731492 0.9998199 0.007771995
vn 0.01087428 0.9998992 0.009137975
vt 0.2616653 1.446398
vt 0.2618052 1.446704
vt 0.2616606 1.446553
vt 0.2615913 1.460558

usemtl physics
f 43986/43986/43986 43987/43987/43987 43988/43988/43988
f 43989/43989/43989 43990/43990/43990 43991/43991/43991
f 43992/43992/43992 43993/43993/43993 43994/43994/43994

"""


@pytest.mark.fast
@pytest.mark.io
@pytest.mark.parametrize(
    "example_type, example_file_input",
    [("wall", wall_example), ("track", track_example)],
)
def test_monza_group_names(example_type: str, example_file_input: str):
    obj_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
    obj_file.write(example_file_input)
    obj_file.close()

    track = Monza(obj_file.name)

    if example_type == "wall":
        assert track.group_names == {"wall"}
        assert track.group_name_to_obj_group.get("wall") == {"09WALL002"}
    elif example_type == "track":
        assert track.group_names == {"asph"}
        assert track.group_name_to_obj_group.get("asph") == {"14MONZA-ASPH6548"}

    os.remove(obj_file.name)


@pytest.mark.fast
@pytest.mark.io
@pytest.mark.parametrize(
    "example_type, example_file_input",
    [("wall", wall_example), ("track", track_example)],
)
def test_monza_get_walls(example_type: str, example_file_input: str):
    obj_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
    obj_file.write(wall_example)
    obj_file.close()

    if example_type == "wall":
        track = Monza(obj_file.name)
        expected_walls = [
            {
                "group_name": "09WALL002",
                "vertices": [
                    (-216.9998, -9.689583, 748.7813),
                    (-219.1955, -6.713692, 731.4688),
                    (-216.9998, -6.689583, 748.7813),
                ],
            },
        ]

        assert track.get_walls == expected_walls

    elif example_type == "track":
        track = Monza(obj_file.name)
        assert track.group_names == {"asph"}
        assert track.get_walls == []

    os.remove(obj_file.name)


if __name__ == "__main__":
    # TODO(adrian): implement get walls
    pytest.main()
