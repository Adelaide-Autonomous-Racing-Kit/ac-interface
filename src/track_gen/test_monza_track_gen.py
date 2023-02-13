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

longer_wall_example = """g 09WALL002
v -216.9998 -9.689583 748.7813
v -219.1955 -6.713692 731.4688
v -216.9998 -6.689583 748.7813
vn 0.9920538 7.703942E-18 -0.1258149
vn 0.9920538 7.703942E-18 -0.1258149
vn 0.9920537 7.703942E-18 -0.1258149
vt 0.1162915 1.063541
vt 0.1162492 1.063478
vt 0.1162915 1.063541

usemtl physics
f 53915/53915/53915 53916/53916/53916 53917/53917/53917
f 53916/53916/53916 53915/53915/53915 53918/53918/53918
f 53919/53919/53919 53920/53920/53920 53921/53921/53921

g 10WALL003
v -200.4553 -8.034454 280.9923
v -199.1033 -8.011131 266.5859
v -200.4553 -5.034454 280.9923
vn 0.9956255 -5.721158E-18 0.09343361
vn 0.9956256 -5.721159E-18 0.09343362
vn 0.9956256 -5.721159E-18 0.09343362
vt 0.1166099 1.061855
vt 0.116636 1.061803
vt 0.1166099 1.061855

usemtl physics
f 54245/54245/54245 54246/54246/54246 54247/54247/54247
f 54248/54248/54248 54247/54247/54247 54246/54246/54246
f 54249/54249/54249 54250/54250/54250 54251/54251/54251
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

longer_track_example = """g 14MONZA-ASPH6548
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

g 15MONZA-ASPH2234
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
    "example_id, example_file_input",
    [
        ("wall", wall_example),
        ("longer_wall", longer_wall_example),
        ("track", track_example),
        ("longer_track", longer_track_example),
    ],
)
def test_monza_group_names(example_id: str, example_file_input: str):
    obj_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
    obj_file.write(example_file_input)
    obj_file.close()

    track = Monza(obj_file.name)

    if example_id == "wall":
        assert track.group_names == {"wall"}
        assert track.group_name_to_obj_group.get("wall") == {"09WALL002"}
    elif example_id == "longer_wall":
        assert track.group_names == {"wall"}
        assert track.group_name_to_obj_group.get("wall") == {"09WALL002", "10WALL003"}
    elif example_id == "track":
        assert track.group_names == {"asph"}
        assert track.group_name_to_obj_group.get("asph") == {"14MONZA-ASPH6548"}
    elif example_id == "longer_track":
        assert track.group_names == {"asph"}
        assert track.group_name_to_obj_group.get("asph") == {
            "14MONZA-ASPH6548",
            "15MONZA-ASPH2234",
        }

    os.remove(obj_file.name)


@pytest.mark.fast
@pytest.mark.io
@pytest.mark.parametrize(
    "example_id, example_file_input",
    [
        ("wall", wall_example),
        ("longer_wall", longer_wall_example),
        ("track", track_example),
        ("longer_track", longer_track_example),
    ],
)
def test_monza_walls(example_id: str, example_file_input: str):
    obj_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
    obj_file.write(example_file_input)
    obj_file.close()

    track = Monza(obj_file.name)

    if example_id == "wall":
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
        assert track.walls == expected_walls

    elif example_id == "longer_wall":
        expected_walls = [
            {
                "group_name": "09WALL002",
                "vertices": [
                    (-216.9998, -9.689583, 748.7813),
                    (-219.1955, -6.713692, 731.4688),
                    (-216.9998, -6.689583, 748.7813),
                ],
            },
            {
                "group_name": "10WALL003",
                "vertices": [
                    (-200.4553, -8.034454, 280.9923),
                    (-199.1033, -8.011131, 266.5859),
                    (-200.4553, -5.034454, 280.9923),
                ],
            },
        ]
        assert track.walls == expected_walls

    elif example_id == "track":
        assert track.group_names == {"asph"}
        assert track.walls == []

    elif example_id == "longer_track":
        assert track.group_names == {"asph"}
        assert track.walls == []

    os.remove(obj_file.name)


if __name__ == "__main__":
    # TODO(adrian): visualise track
    pytest.main()
