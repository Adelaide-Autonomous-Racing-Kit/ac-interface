from dataclasses import dataclass
from typing import Dict, List

from src.tools.data_generation.tracks.constants import SEMANTIC_NAME_TO_ID


@dataclass
class TrackData:
    geometries_to_remove: List[str]
    vertex_groups_to_modify: List[str]
    material_to_semantics: Dict[str, str]

    def __post_init__(self):
        self.material_to_id = {
            material: SEMANTIC_NAME_TO_ID[semantic_name]
            for material, semantic_name in self.material_to_semantics.items()
        }
