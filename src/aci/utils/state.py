from __future__ import annotations

from aci.utils.ins import SimulatedINS
from aci.utils.load import state_bytes_to_dict


def process_state(state: bytes, ins: SimulatedINS) -> Dict:
    state = state_bytes_to_dict(state)
    return state


def simulate_ins_readings(state: Dict, ins: SimulatedINS) -> Dict:
    state = state_bytes_to_dict(state)
    ins(state)
    return state


def identity(state: bytes, ins: SimulatedINS) -> bytes:
    return state
