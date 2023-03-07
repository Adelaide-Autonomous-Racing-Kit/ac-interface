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

MESH_NAME_TO_SEMANTIC_CLASS = {
    # "a": "vegetation",
    # "aa": "vegetation",
    "accrewloda": "people",
    "accrewlodb": "people",
    "ambulance": "vehicle",
    "aspgrp": "road",
    "asphshd": "road",
    "asphdrk": "road",
    # "b": "vegetation",
    "box": "structure",
    "boxbottom": "structure",
    "boxconc": "structure",
    "boxmtlprtc": "structure",
    "boxparall": "structure",
    "boxparhi": "structure",
    "boxparlow": "structure",
    "boxparmid": "structure",
    "bridgebase": "structure",
    "bridgedetailhi": "structure",
    "bridgelow": "structure",
    "bullonshikslayer": "structure",
    # "c": "vegetation",
    "camerafacingkslayer": "structure",
    "car": "vehicle",
    "concpits": "road",
    "crbshd": "curb",
    "curbgrp": "curb",
    "cylinder": "structure",
    # "d": "vegetation",
    # "e": "vegetation",
    # "ext": "vegetation",
    # "f": "vegetation",
    "fence": "structure",
    "flag": "structure",
    "flagt": "structure",
    # "g": "vegetation",
    "giuntihikslayer": "structure",
    "grailhi": "structure",
    "graillow": "structure",
    "grsshd": "grass",
    # "h": "vegetation",
    "hedge": "vegetation",
    "hi": "structure",
    # "i": "vegetation",
    # "j": "vegetation",
    "jointmid": "structure",
    # "k": "vegetation",
    # "l": "vegetation",
    "line": "structure",
    "loft": "structure",
    "low": "structure",
    # "m": "vegetation",
    "mainpole": "structure",
    "marshallhia": "people",
    "marshallhib": "people",
    "marshallhic": "people",
    "marshalllowa": "people",
    "marshalllowb": "people",
    "marshalllowc": "people",
    "mesh": "structure",
    "metals": "structure",
    "object": "structure",
    "objectsub": "structure",
    "padd": "structure",
    "parab": "road",
    "passhi": "structure",
    "passlow": "structure",
    "passmid": "structure",
    "poledetailhi": "structure",
    "poledetailmid": "structure",
    "postbluhi": "structure",
    "railclone": "structure",
    "shadowserraglio": "road",
    "shape": "structure",
    "shaps": "structure",
    # "sand": "sand",
    "sndgrp": "sand",
    "standhi": "structure",
    "standlow": "structure",
    "standmid": "structure",
    "structures": "structure",
    # "t": "vegetation",
    "terrain": "structure",
    "treed": "vegetation",
    # "treeshadow": "vegetation",
    "tribasc": "structure",
    "triblesmo": "structure",
    # "u": "vegetation",
    # "v": "vegetation",
    "veichles": "vehicle",
    "whline": "track_limit",
    # "z": "vegetation",
    # "painted": "road",
}


MESH_NAME_TO_ID = {
    mesh_name: SEMANTIC_NAME_TO_ID[semantic_name]
    for mesh_name, semantic_name in MESH_NAME_TO_SEMANTIC_CLASS.items()
}
