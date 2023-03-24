from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class ClassInformation:
    name: str
    train_id: int
    colour: Tuple[int]


SEMANTIC_CLASSES = [
    ClassInformation("road", 0, (84, 84, 84)),
    ClassInformation("curb", 1, (255, 119, 51)),
    ClassInformation("track_limit", 2, (255, 255, 255)),
    ClassInformation("sand", 3, (255, 255, 0)),
    ClassInformation("grass", 4, (170, 255, 128)),
    ClassInformation("vehicle", 5, (255, 42, 0)),
    ClassInformation("structure", 6, (153, 153, 255)),
    ClassInformation("vegetation", 7, (0, 102, 17)),
    ClassInformation("people", 8, (255, 179, 204)),
    ClassInformation("void", -1, (0, 0, 0)),
]

SEMANTIC_NAME_TO_COLOUR = {info.name: info.colour for info in SEMANTIC_CLASSES}
SEMANTIC_NAME_TO_ID = {info.name: info.train_id for info in SEMANTIC_CLASSES}

COLOUR_LIST = [
    info.colour
    for info in sorted(SEMANTIC_CLASSES, key=lambda x: x.train_id)
    if info.train_id > -1
]
COLOUR_LIST.append(SEMANTIC_CLASSES[-1].colour)
COLOUR_LIST = np.asarray(COLOUR_LIST, dtype=np.uint8)

TRAIN_ID_LIST = [
    info.train_id
    for info in sorted(SEMANTIC_CLASSES, key=lambda x: x.train_id)
    if info.train_id > -1
]
TRAIN_ID_LIST.append(SEMANTIC_CLASSES[-1].train_id)
TRAIN_ID_LIST = np.asarray(TRAIN_ID_LIST, dtype=np.uint8)

GEOMETRIES_TO_REMOVE = [
    "shadow_serraglio",
    "groove2",
    "groove",
    "groove2b",
    "tree_shadow",
    "horizont",
    "physics",
    "trees",
    "tree8",
    "misc_alphatest",
    "treesline",
    "branch5",
    "hedge",
    "bushes",
    "misc_alpha",
    "Bark",
    "antennas",
]

MATERIAL_TO_SEMANTIC_CLASS = {
    "Pannello_Skin_00": "structure",
    "driver_face": "people",
    "driver_suit": "people",
    "Pitlane_Props_BASE": "structure",
    "whiteline": "track_limit",
    "grs_brd": "grass",
    "brd2": "road",
    "gstand-alpha": "structure",
    # "antennas": "structure",
    # "treesline": "vegetation",
    "fences2": "structure",
    "fences1": "structure",
    # "hedge": "vegetation",
    "paddk": "structure",
    "metals-alpha": "structure",
    # "branch5": "vegetation",
    # "trees": "vegetation",
    # "tree8": "vegetation",
    # "misc_alphatest": "vegetation",
    "serraglio": "structure",
    "flag1": "structure",
    "flag3": "structure",
    "flag4": "structure",
    "flag5": "structure",
    "flag6": "structure",
    "flag2": "structure",
    "flag7": "structure",
    "flag8": "structure",
    "top_new": "grass",
    "top_B": "grass",
    "apsh-shader-norm": "road",
    "asph-pitlane": "road",
    "grass-shader": "grass",
    "apsh-shader-mid": "road",
    "curb-NM": "curb",
    "curb-shader": "curb",
    "apsh-shader2": "road",
    "apsh-shader-scuro": "road",
    "gstand": "structure",
    "BBgrass": "grass",
    # "bushes": "vegetation",
    "lights": "structure",
    # "misc_alpha": "vegetation",
    "objects1": "vehicle",
    "marshall": "people",
    "Vehicles": "vehicle",
    "adv_add": "structure",
    "walls": "structure",
    "box_M": "structure",
    "metals": "structure",
    "tyres": "structure",
    "bridges": "structure",
    "wall2": "structure",
    "grille": "curb",
    # "Bark": "vegetation",
    "MB_Sprinter_2014": "vehicle",
    "box": "structure",
    "sand": "sand",
    "billboards": "structure",
    "glass": "structure",
    "glass_B": "structure",
    "misc1": "structure",
}

VERTEX_GROUPS_TO_MODIFY = [
    "AC_PIT",
    "AC_START",
    "AC_AUDIO",
    "HOT_LAP_START",
    "AC_POBJECT",
    "AC_TIME_ATTACK",
]

MESH_NAME_TO_ID = {
    mesh_name: SEMANTIC_NAME_TO_ID[semantic_name]
    for mesh_name, semantic_name in MATERIAL_TO_SEMANTIC_CLASS.items()
}
